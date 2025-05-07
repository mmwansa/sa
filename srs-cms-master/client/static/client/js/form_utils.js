function confirmCancelBack(fallbackUrl = null) {
    if (confirm("Are you sure you want to cancel? Unsaved changes will be lost.")) {
        if (window.history.length > 1) {
            window.history.back();
        } else if (fallbackUrl) {
            window.location.href = fallbackUrl;
        }
    }
}

function navigateBack(fallbackUrl = null) {
    if (window.history.length > 1) {
        window.history.back();
    } else if (fallbackUrl) {
        window.location.href = fallbackUrl;
    }
}