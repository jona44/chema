# feeds/management/commands/manage_feeds.py
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from feeds.models import Feed, Post, PostMedia, FeedActivity, Comment, PostLike
from group.models import Group


class Command(BaseCommand):
    help = 'Management commands for the feeds system'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=[
                'create_feeds', 'cleanup_media', 'update_counts', 
                'moderate_posts', 'analytics', 'migrate_memorial'
            ],
            help='Action to perform'
        )
        
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days for cleanup operations'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        
        parser.add_argument(
            '--group-id',
            type=str,
            help='Specific group ID for targeted operations'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'create_feeds':
            self.create_missing_feeds(options)
        elif action == 'cleanup_media':
            self.cleanup_unused_media(options)
        elif action == 'update_counts':
            self.update_engagement_counts(options)
        elif action == 'moderate_posts':
            self.auto_moderate_posts(options)
        elif action == 'analytics':
            self.show_analytics(options)
        elif action == 'migrate_memorial':
            self.migrate_memorial_posts(options)

    def create_missing_feeds(self, options):
        """Create Feed objects for groups that don't have them"""
        self.stdout.write('Creating missing feeds for groups...')
        
        # Find groups without feeds
        groups_without_feeds = Group.objects.filter(feed__isnull=True)
        
        if options['group_id']:
            groups_without_feeds = groups_without_feeds.filter(pk=options['group_id'])
        
        created_count = 0
        
        for group in groups_without_feeds:
            if not options['dry_run']:
                feed = Feed.objects.create(
                    group=group,
                    allow_posts=True,
                    allow_media=True,
                    allow_polls=group.category != 'memorial',  # Disable polls for memorial groups by default
                    allow_events=True,
                    allow_anonymous_posts=group.category == 'memorial',  # Allow anonymous for memorial
                    require_approval=group.is_private,  # Require approval for private groups # type: ignore
                )
                self.stdout.write(f'  ✓ Created feed for group: {group.name}')
                created_count += 1
            else:
                self.stdout.write(f'  → Would create feed for group: {group.name}')
        
        if options['dry_run']:
            self.stdout.write(f'Would create {groups_without_feeds.count()} feeds')
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {created_count} feeds')
            )

    def cleanup_unused_media(self, options):
        """Clean up orphaned media files and old temporary files"""
        self.stdout.write('Cleaning up unused media files...')
        
        days_ago = timezone.now() - timedelta(days=options['days'])
        
        # Find orphaned media (posts deleted but media remains)
        orphaned_media = PostMedia.objects.filter(
            post__isnull=True
        ) | PostMedia.objects.filter(
            uploaded_at__lt=days_ago,
            post__isnull=True
        )
        
        if options['group_id']:
            orphaned_media = orphaned_media.filter(
                post__feed__group_id=options['group_id']
            )
        
        total_size = 0
        deleted_count = 0
        
        for media in orphaned_media:
            if media.file:
                try:
                    file_size = media.file.size
                    total_size += file_size
                    
                    if not options['dry_run']:
                        media.file.delete()
                        media.delete()
                        self.stdout.write(f'  ✓ Deleted: {media.file.name}')
                    else:
                        self.stdout.write(f'  → Would delete: {media.file.name}')
                    
                    deleted_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Error deleting {media.file.name}: {e}')
                    )
        
        # Convert bytes to readable format
        if total_size > 1024 * 1024 * 1024:  # GB
            size_str = f'{total_size / (1024**3):.2f} GB'
        elif total_size > 1024 * 1024:  # MB
            size_str = f'{total_size / (1024**2):.2f} MB'
        else:
            size_str = f'{total_size / 1024:.2f} KB'
        
        if options['dry_run']:
            self.stdout.write(f'Would delete {deleted_count} files ({size_str})')
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Cleaned up {deleted_count} files ({size_str})')
            )

    def update_engagement_counts(self, options):
        """Recalculate engagement counts for posts"""
        self.stdout.write('Updating engagement counts...')
        
        posts_query = Post.objects.all()
        
        if options['group_id']:
            posts_query = posts_query.filter(feed__group_id=options['group_id'])
        
        updated_count = 0
        
        for post in posts_query:
            if not options['dry_run']:
                # Recalculate counts
                post.likes_count = post.likes.count() # type: ignore
                post.comments_count = post.comments.count() # type: ignore
                post.shares_count = post.shares.count() # type: ignore
                
                # Update views from activity log
                views_count = FeedActivity.objects.filter(
                    post=post,
                    activity_type='view'
                ).values('user').distinct().count()
                post.views_count = views_count
                
                post.save(update_fields=[
                    'likes_count', 'comments_count', 'shares_count', 'views_count'
                ])
                
                updated_count += 1
            else:
                self.stdout.write(f'  → Would update post: {post.title or post.content[:50]}')
        
        if options['dry_run']:
            self.stdout.write(f'Would update {posts_query.count()} posts')
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Updated engagement counts for {updated_count} posts')
            )

    def auto_moderate_posts(self, options):
        """Auto-moderate posts based on keywords and patterns"""
        self.stdout.write('Running auto-moderation...')
        
        # Find posts that need moderation
        pending_posts = Post.objects.filter(
            is_approved=False,
            is_flagged=False
        )
        
        if options['group_id']:
            pending_posts = pending_posts.filter(feed__group_id=options['group_id'])
        
        approved_count = 0
        flagged_count = 0
        
        for post in pending_posts:
            feed = post.feed
            should_flag = False
            flag_reason = ''
            
            # Check for moderation keywords
            if feed.auto_moderate_keywords:
                keywords = [k.strip().lower() for k in feed.auto_moderate_keywords.split(',')]
                content_lower = (post.title + ' ' + post.content).lower()
                
                for keyword in keywords:
                    if keyword in content_lower:
                        should_flag = True
                        flag_reason = f'Contains flagged keyword: {keyword}'
                        break
            
            # Check for spam patterns
            if not should_flag:
                # Too many links
                if post.content.count('http') > 3:
                    should_flag = True
                    flag_reason = 'Too many links (possible spam)'
                
                # Too much capitalization
                elif sum(1 for c in post.content if c.isupper()) > len(post.content) * 0.7:
                    should_flag = True
                    flag_reason = 'Excessive capitalization'
            
            if not options['dry_run']:
                if should_flag:
                    post.is_flagged = True
                    post.flagged_reason = flag_reason
                    post.save(update_fields=['is_flagged', 'flagged_reason'])
                    flagged_count += 1
                    self.stdout.write(f'  ⚠ Flagged: {flag_reason}')
                else:
                    post.is_approved = True
                    post.save(update_fields=['is_approved'])
                    approved_count += 1
                    self.stdout.write(f'  ✓ Approved post from {post.author.email}')
            else:
                if should_flag:
                    self.stdout.write(f'  → Would flag: {flag_reason}')
                else:
                    self.stdout.write(f'  → Would approve post from {post.author.email}')
        
        if options['dry_run']:
            self.stdout.write(f'Would process {pending_posts.count()} posts')
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Auto-moderation complete: {approved_count} approved, {flagged_count} flagged'
                )
            )

    def show_analytics(self, options):
        """Show analytics about feeds usage"""
        self.stdout.write('Feed Analytics Report')
        self.stdout.write('=' * 50)
        
        # Overall stats
        total_feeds = Feed.objects.count()
        total_posts = Post.objects.filter(is_approved=True).count()
        total_comments = Comment.objects.filter(is_approved=True).count()
        total_likes = PostLike.objects.count()
        
        self.stdout.write(f'Total Feeds: {total_feeds}')
        self.stdout.write(f'Total Posts: {total_posts}')
        self.stdout.write(f'Total Comments: {total_comments}')
        self.stdout.write(f'Total Likes: {total_likes}')
        self.stdout.write('')
        
        # Most active groups
        self.stdout.write('Most Active Groups:')
        active_groups = Feed.objects.annotate(
            post_count=Count('posts', filter=Q(posts__is_approved=True))
        ).order_by('-post_count')[:10]
        
        for i, feed in enumerate(active_groups, 1):
            self.stdout.write(f'  {i}. {feed.group.name}: {feed.post_count} posts') # type: ignore
        
        self.stdout.write('')
        
        # Post types breakdown
        self.stdout.write('Post Types:')
        post_types = Post.objects.filter(is_approved=True).values('post_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        for pt in post_types:
            type_display = dict(Post.POST_TYPES).get(pt['post_type'], pt['post_type'])
            self.stdout.write(f'  {type_display}: {pt["count"]}')
        
        self.stdout.write('')
        
        # Recent activity (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        recent_posts = Post.objects.filter(
            created_at__gte=week_ago,
            is_approved=True
        ).count()
        recent_comments = Comment.objects.filter(
            created_at__gte=week_ago,
            is_approved=True
        ).count()
        
        self.stdout.write('Recent Activity (Last 7 Days):')
        self.stdout.write(f'  New Posts: {recent_posts}')
        self.stdout.write(f'  New Comments: {recent_comments}')
        
        # Memorial integration stats
        memorial_posts = Post.objects.filter(
            memorial_related__isnull=False,
            is_approved=True
        ).count()
        
        if memorial_posts > 0:
            self.stdout.write('')
            self.stdout.write('Memorial Integration:')
            self.stdout.write(f'  Memorial Posts: {memorial_posts}')
            
            memorial_types = Post.objects.filter(
                memorial_related__isnull=False,
                is_approved=True
            ).values('post_type').annotate(count=Count('id'))
            
            for mt in memorial_types:
                type_display = dict(Post.POST_TYPES).get(mt['post_type'], mt['post_type'])
                self.stdout.write(f'    {type_display}: {mt["count"]}')

    def migrate_memorial_posts(self, options):
        """Migrate existing memorial posts to the feeds system"""
        self.stdout.write('Migrating memorial posts to feeds system...')
        
        try:
            from memorial.models import Memorial,Post as MemorialPost
        except ImportError:
            self.stdout.write(
                self.style.ERROR('Memorial app not found. Skipping migration.')
            )
            return
        
        # Find memorial groups that need migration
        memorials = Memorial.objects.all()
        
        if options['group_id']:
            memorials = memorials.filter(associated_group_id=options['group_id'])
        
        migrated_count = 0
        
        for memorial in memorials:
            # Ensure the memorial group has a feed
            feed, created = Feed.objects.get_or_create(
                group=memorial.associated_group,
                defaults={
                    'allow_posts': True,
                    'allow_media': True,
                    'allow_polls': False,
                    'allow_events': True,
                    'allow_anonymous_posts': True,
                }
            )
            
            # Migrate memorial posts if they exist
            if hasattr(memorial, 'posts'):
                memorial_posts = memorial.posts.all() # type: ignore
                
                for mem_post in memorial_posts:
                    if not options['dry_run']:
                        # Create new feed post
                        feed_post = Post.objects.create(
                            author=mem_post.author,
                            feed=feed,
                            post_type=mem_post.post_type,
                            title=mem_post.title,
                            content=mem_post.content,
                            is_anonymous=mem_post.is_anonymous,
                            is_pinned=mem_post.is_pinned,
                            memorial_related=memorial,
                            created_at=mem_post.created_at,
                            updated_at=mem_post.updated_at,
                        )
                        
                        # Migrate media if exists
                        if hasattr(mem_post, 'images'):
                            for image in mem_post.images.all():
                                PostMedia.objects.create(
                                    post=feed_post,
                                    media_type='image',
                                    file=image.image,
                                    caption=image.caption,
                                    uploaded_by=image.uploaded_by,
                                    uploaded_at=image.uploaded_at,
                                )
                        
                        migrated_count += 1
                        self.stdout.write(f'  ✓ Migrated: {mem_post.title or "Untitled"}')
                    else:
                        self.stdout.write(f'  → Would migrate: {mem_post.title or "Untitled"}')
        
        if options['dry_run']:
            self.stdout.write(f'Would migrate posts from {memorials.count()} memorials')
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully migrated {migrated_count} memorial posts')
            )