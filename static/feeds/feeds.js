  <!-- Scripts -->
    <script>
        // Re-initialize Flowbite after HTMX swaps
        document.body.addEventListener('htmx:afterSwap', function (event) {
            if (window.initFlowbite) {
                window.initFlowbite();
            }
        });

        // Pre-select post type in modal
        document.addEventListener('click', function (e) {
            const toggleButton = e.target.closest('[data-modal-toggle="create-post-modal"]');
            if (toggleButton && toggleButton.dataset.postType) {
                const postType = toggleButton.dataset.postType;
                const modal = document.getElementById('create-post-modal');
                if (modal) {
                    const postTypeSelect = modal.querySelector('select[name="post_type"]');
                    if (postTypeSelect) {
                        postTypeSelect.value = postType;
                    }
                }
            }
        });

        function toggleReplyForm(commentId) {
            const form = document.getElementById('reply-form-' + commentId);
            if (form) {
                form.classList.toggle('hidden');
                if (!form.classList.contains('hidden')) {
                    form.querySelector('textarea').focus();
                }
            }
        }

        function sharePost(button) {
            const postUrl = button.dataset.postUrl;
            const postTitle = button.dataset.postTitle;
            const shareText = button.querySelector('.share-text');
            const successText = button.querySelector('.share-success-text');

            if (navigator.share) {
                navigator.share({
                    title: postTitle,
                    text: `Check out this post on Chema!`,
                    url: postUrl,
                })
                .then(() => console.log('Successful share'))
                .catch((error) => console.log('Error sharing', error));
            } else {
                navigator.clipboard.writeText(postUrl).then(function () {
                    if (shareText && successText) {
                        shareText.classList.add('hidden');
                        successText.classList.remove('hidden');
                        setTimeout(() => {
                            shareText.classList.remove('hidden');
                            successText.classList.add('hidden');
                        }, 2000);
                    }
                }, function (err) {
                    console.error('Could not copy text: ', err);
                    alert('Failed to copy link.');
                });
            }
        }

        // CSRF token for HTMX
        document.body.addEventListener('htmx:configRequest', (event) => {
            const token = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            event.detail.headers['X-CSRFToken'] = token;
        });

        // Lightbox JavaScript (from previous artifact)
        let currentPostMedia = [];
        let currentMediaIndex = 0;
        let currentPostId = null;

        function openLightbox(postId, startIndex) {
            collectPostMedia(postId);
            if (currentPostMedia.length === 0) return;
            
            currentMediaIndex = startIndex;
            currentPostId = postId;
            
            const lightbox = document.getElementById('media-lightbox');
            const prevBtn = document.getElementById('lightbox-prev');
            const nextBtn = document.getElementById('lightbox-next');
            
            if (currentPostMedia.length > 1) {
                prevBtn.classList.remove('hidden');
                nextBtn.classList.remove('hidden');
            } else {
                prevBtn.classList.add('hidden');
                nextBtn.classList.add('hidden');
            }
            
            loadMediaAtIndex(currentMediaIndex);
            lightbox.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }

        function collectPostMedia(postId) {
            currentPostMedia = [];
            const postContainer = document.querySelector(`[data-post-id="${postId}"]`);
            if (!postContainer) return;
            
            const mediaElements = postContainer.querySelectorAll('[data-media-url]');
            mediaElements.forEach(element => {
                currentPostMedia.push({
                    url: element.dataset.mediaUrl,
                    altText: element.dataset.mediaAlt || '',
                    type: element.dataset.mediaType || 'image',
                    caption: element.dataset.mediaCaption || ''
                });
            });
        }

        function loadMediaAtIndex(index) {
            if (index < 0 || index >= currentPostMedia.length) return;
            
            const media = currentPostMedia[index];
            const image = document.getElementById('lightbox-image');
            const video = document.getElementById('lightbox-video');
            const caption = document.getElementById('lightbox-caption');
            const counter = document.getElementById('lightbox-counter');
            const download = document.getElementById('lightbox-download');
            
            video.pause();
            video.currentTime = 0;
            
            if (media.type === 'image') {
                image.src = media.url;
                image.alt = media.altText;
                image.classList.remove('hidden');
                video.classList.add('hidden');
            } else if (media.type === 'video') {
                video.querySelector('source').src = media.url;
                video.load();
                video.classList.remove('hidden');
                image.classList.add('hidden');
            }
            
            caption.textContent = media.caption || media.altText || '';
            counter.textContent = currentPostMedia.length > 1 ? `${index + 1} / ${currentPostMedia.length}` : '';
            download.href = media.url;
            download.download = media.url.split('/').pop();
        }

        function closeLightbox() {
            const lightbox = document.getElementById('media-lightbox');
            const video = document.getElementById('lightbox-video');
            const image = document.getElementById('lightbox-image');
            
            video.pause();
            video.currentTime = 0;
            image.src = '';
            video.querySelector('source').src = '';
            
            lightbox.classList.add('hidden');
            document.body.style.overflow = 'auto';
            
            currentPostMedia = [];
            currentMediaIndex = 0;
            currentPostId = null;
        }

        function navigateLightbox(direction) {
            if (currentPostMedia.length === 0) return;
            currentMediaIndex = (currentMediaIndex + direction + currentPostMedia.length) % currentPostMedia.length;
            loadMediaAtIndex(currentMediaIndex);
        }

        // Keyboard navigation
        document.addEventListener('keydown', function(e) {
            const lightbox = document.getElementById('media-lightbox');
            if (!lightbox.classList.contains('hidden')) {
                e.preventDefault();
                if (e.key === 'Escape') closeLightbox();
                else if (e.key === 'ArrowLeft') navigateLightbox(-1);
                else if (e.key === 'ArrowRight') navigateLightbox(1);
            }
        });
    </script>

