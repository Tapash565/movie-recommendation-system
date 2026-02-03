// Toast notification
function showToast(message) {
    var x = document.getElementById("toast");
    x.textContent = message;
    x.className = "toast show";
    setTimeout(function () { x.className = x.className.replace("show", ""); }, 3000);
}

async function toggleBookmark(movie_id, movie_title, status) {
    try {
        const response = await fetch('/api/bookmark', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                movie_id: parseInt(movie_id),
                movie_title: movie_title,
                status: status
            })
        });

        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                showToast(status === 'to_watch' ? "Added to Watchlist!" : "Marked as Watched!");
                location.reload(); // Reload to update UI state
            } else {
                showToast("Failed to update bookmark.");
            }
        } else {
            showToast("Please login first.");
            window.location.href = "/login";
        }
    } catch (error) {
        console.error('Error:', error);
        showToast("An error occurred.");
    }
}

async function removeBookmark(movie_id) {
    try {
        const response = await fetch('/api/remove_bookmark', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                movie_id: parseInt(movie_id)
            })
        });

        if (response.ok) {
            showToast("Removed from library.");
            location.reload();
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function saveRating(movie_id, movie_title) {
    const rating = document.getElementById('rating-slider').value;
    try {
        const response = await fetch('/api/rate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                movie_id: parseInt(movie_id),
                movie_title: movie_title,
                rating: parseFloat(rating)
            })
        });

        if (response.ok) {
            showToast("Rating saved: " + rating + "/10");
        } else {
            showToast("Please login first.");
            window.location.href = "/login";
        }
    } catch (error) {
        console.error('Error:', error);
        showToast("An error occurred.");
    }
}

// Update rating value display on slide
document.addEventListener('DOMContentLoaded', function () {
    const slider = document.getElementById('rating-slider');
    const display = document.getElementById('rating-value');
    if (slider && display) {
        slider.oninput = function () {
            display.innerHTML = this.value;
        }
    }
});
