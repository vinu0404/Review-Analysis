/**
 * AI Feedback System - User Dashboard
 * Handles review submission, star rating, and API communication
 */

const API_BASE_URL = window.location.origin;
const API_ENDPOINTS = {
    submitReview: `${API_BASE_URL}/api/user/submit-review`,
    health: `${API_BASE_URL}/api/user/health`
};

const RATING_TEXTS = {
    0: 'Click to rate',
    1: 'Poor - Very disappointed',
    2: 'Below Average - Could be better',
    3: 'Average - It was okay',
    4: 'Good - Satisfied',
    5: 'Excellent - Exceeded expectations!'
};

let selectedRating = 0;

const reviewForm = document.getElementById('review-form');
const starRating = document.getElementById('star-rating');
const stars = starRating.querySelectorAll('.star');
const ratingInput = document.getElementById('rating-value');
const ratingText = document.getElementById('rating-text');
const reviewTextarea = document.getElementById('review-text');
const charCount = document.getElementById('char-count');
const charCounter = document.querySelector('.char-counter');
const submitBtn = document.getElementById('submit-btn');
const btnText = submitBtn.querySelector('.btn-text');
const btnLoader = submitBtn.querySelector('.btn-loader');
const reviewCard = document.querySelector('.review-card');
const responseCard = document.getElementById('response-card');
const aiResponse = document.getElementById('ai-response');
const responseMeta = document.getElementById('response-meta');
const newReviewBtn = document.getElementById('new-review-btn');
const errorToast = document.getElementById('error-toast');
const errorMessage = document.getElementById('error-message');
const toastClose = document.getElementById('toast-close');
const successToast = document.getElementById('success-toast');

document.addEventListener('DOMContentLoaded', () => {
    initStarRating();
    initTextarea();
    initForm();
    initToasts();
});

function initStarRating() {
    stars.forEach((star, index) => {
        star.addEventListener('mouseenter', () => {
            highlightStars(index + 1);
        });

        star.addEventListener('click', () => {
            selectRating(index + 1);
        });
    });

    starRating.addEventListener('mouseleave', () => {
        highlightStars(selectedRating);
    });
}

function highlightStars(value) {
    stars.forEach((star, index) => {
        if (index < value) {
            star.classList.add('hover');
        } else {
            star.classList.remove('hover');
        }
    });
}

function selectRating(value) {
    selectedRating = value;
    ratingInput.value = value;
    stars.forEach((star, index) => {
        if (index < value) {
            star.classList.add('selected');
        } else {
            star.classList.remove('selected');
        }
    });
    ratingText.textContent = RATING_TEXTS[value];
    ratingText.classList.add('selected');

    validateForm();
}

function initTextarea() {
    reviewTextarea.addEventListener('input', () => {
        updateCharCount();
        validateForm();
    });
    updateCharCount();
}

function updateCharCount() {
    const count = reviewTextarea.value.length;
    charCount.textContent = count;
    charCounter.classList.remove('warning', 'error');
    
    if (count > 900) {
        charCounter.classList.add('warning');
    }
    if (count >= 1000) {
        charCounter.classList.add('error');
    }
    reviewTextarea.classList.remove('invalid', 'valid');
    
    if (count > 0 && count < 10) {
        reviewTextarea.classList.add('invalid');
    } else if (count >= 10) {
        reviewTextarea.classList.add('valid');
    }
}

function validateForm() {
    const isRatingValid = selectedRating >= 1 && selectedRating <= 5;
    const isTextValid = reviewTextarea.value.trim().length >= 10;
    const isValid = isRatingValid && isTextValid;

    submitBtn.disabled = !isValid;

    return isValid;
}

function initForm() {
    reviewForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!validateForm()) {
            showError('Please provide a rating and write at least 10 characters.');
            return;
        }

        await submitReview();
    });

    newReviewBtn.addEventListener('click', resetForm);
}


async function submitReview() {
    setLoadingState(true);

    const payload = {
        rating: selectedRating,
        review_text: reviewTextarea.value.trim()
    };

    try {
        const response = await fetch(API_ENDPOINTS.submitReview, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showResponse(data);
        } else {
            const errorMsg = data.detail || data.error || 'Failed to submit review';
            showError(errorMsg);
        }
    } catch (error) {
        console.error('Submit error:', error);
        showError('Network error. Please check your connection and try again.');
    } finally {
        setLoadingState(false);
    }
}

function showResponse(data) {
    reviewCard.style.display = 'none';

    aiResponse.textContent = data.user_response;
    responseMeta.innerHTML = `
        Submission ID: <strong>${data.submission_id.slice(-8)}</strong> | 
        Processed in <strong>${data.processing_time_ms}ms</strong>
    `;
    responseCard.style.display = 'block';
    showSuccessToast();
}

function resetForm() {
    selectedRating = 0;
    ratingInput.value = 0;
    reviewTextarea.value = '';

    stars.forEach(star => {
        star.classList.remove('selected', 'hover');
    });
    ratingText.textContent = RATING_TEXTS[0];
    ratingText.classList.remove('selected');

    reviewTextarea.classList.remove('valid', 'invalid');
    updateCharCount();
    submitBtn.disabled = true;
    responseCard.style.display = 'none';
    reviewCard.style.display = 'block';
}

function setLoadingState(loading) {
    if (loading) {
        submitBtn.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'flex';
        reviewTextarea.disabled = true;
    } else {
        submitBtn.disabled = !validateForm();
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
        reviewTextarea.disabled = false;
    }
}

function initToasts() {
    toastClose.addEventListener('click', () => {
        hideError();
    });
}

function showError(message) {
    errorMessage.textContent = message;
    errorToast.style.display = 'flex';
    setTimeout(() => {
        hideError();
    }, 5000);
}

function hideError() {
    errorToast.style.display = 'none';
}

function showSuccessToast() {
    successToast.style.display = 'flex';
    setTimeout(() => {
        successToast.style.display = 'none';
    }, 3000);
}
