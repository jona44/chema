document.addEventListener('DOMContentLoaded', function () {
    const modalElement = document.getElementById('create-post-modal');
    if (!modalElement) {
        return;
    }

    // Options for the Flowbite modal
    const modalOptions = {
        placement: 'center',
        backdrop: 'dynamic',
        backdropClasses: 'bg-gray-900 bg-opacity-50 dark:bg-opacity-80 fixed inset-0 z-40',
        closable: true,
        // This callback function will be executed when the modal is hidden
        onHide: () => {
            // Reset the form after the modal is hidden
            const form = document.getElementById('post-form');
            if (form) {
                form.reset();
            }
            aggressivelyRemoveBackdrops();
        },
    };

    // Create a new Modal instance
    const createPostModal = new Modal(modalElement, modalOptions);

    // Helper to aggressively remove all modal backdrops for 1 second
    function aggressivelyRemoveBackdrops() {
        let elapsed = 0;
        const interval = setInterval(() => {
            document.querySelectorAll('[data-modal-backdrop]').forEach(el => el.remove());
            document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
            elapsed += 100;
            if (elapsed >= 1000) clearInterval(interval);
        }, 100);
    }

    // Function to handle successful post creation
    window.handlePostCreateSuccess = function (event) {
        // Check if the htmx request was successful
        if (event.detail.successful) {
            // Use the Flowbite API to hide the modal
            createPostModal.hide();
            aggressivelyRemoveBackdrops();
        }
    }
});
