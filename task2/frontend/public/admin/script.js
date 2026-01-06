/**
 * AI Feedback System - Admin Dashboard JavaScript
 * Handles authentication, data fetching, and real-time updates
 */

const API_BASE_URL = window.location.origin;
const API_ENDPOINTS = {
    login: `${API_BASE_URL}/api/admin/login`,
    logout: `${API_BASE_URL}/api/admin/logout`,
    reviews: `${API_BASE_URL}/api/admin/reviews`,
    analytics: `${API_BASE_URL}/api/admin/analytics`,
    health: `${API_BASE_URL}/api/admin/health`
};
const CONFIG = {
    refreshInterval: 30000,
    pageSize: 20,
    tokenKey: 'admin_token'
};

let state = {
    token: null,
    currentPage: 1,
    totalPages: 1,
    reviews: [],
    analytics: null,
    filters: {
        rating: '',
        search: ''
    },
    refreshTimer: null,
    countdown: 30
};

let ratingChart = null;
document.addEventListener('DOMContentLoaded', () => {
    const savedToken = localStorage.getItem(CONFIG.tokenKey);
    if (savedToken) {
        state.token = savedToken;
        showDashboard();
        initDashboard();
    } else {
        showLogin();
    }
    initLoginForm();
    initDashboardControls();
    initModal();
});

function initLoginForm() {
    const loginForm = document.getElementById('login-form');
    const loginBtn = document.getElementById('login-btn');
    const loginError = document.getElementById('login-error');

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const password = document.getElementById('password').value;
        setLoginLoading(true);
        loginError.style.display = 'none';

        try {
            const response = await fetch(API_ENDPOINTS.login, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ password })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                state.token = data.token;
                localStorage.setItem(CONFIG.tokenKey, data.token);
                showDashboard();
                initDashboard();
            } else {
                showLoginError(data.detail || 'Invalid password');
            }
        } catch (error) {
            console.error('Login error:', error);
            showLoginError('Network error. Please try again.');
        } finally {
            setLoginLoading(false);
        }
    });
}

function setLoginLoading(loading) {
    const btn = document.getElementById('login-btn');
    const btnText = btn.querySelector('.btn-text');
    const btnLoader = btn.querySelector('.btn-loader');
    
    btn.disabled = loading;
    btnText.style.display = loading ? 'none' : 'inline';
    btnLoader.style.display = loading ? 'flex' : 'none';
}

function showLoginError(message) {
    const loginError = document.getElementById('login-error');
    loginError.textContent = message;
    loginError.style.display = 'block';
}

function showLogin() {
    document.getElementById('login-screen').style.display = 'flex';
    document.getElementById('dashboard').style.display = 'none';
}

function showDashboard() {
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('dashboard').style.display = 'flex';
}

async function logout() {
    try {
        await fetch(API_ENDPOINTS.logout, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });
    } catch (error) {
        console.error('Logout error:', error);
    }

    state.token = null;
    localStorage.removeItem(CONFIG.tokenKey);
    stopAutoRefresh();
    showLogin();
    document.getElementById('password').value = '';
}

function initDashboard() {
    loadAnalytics();
    loadReviews();
    startAutoRefresh();
}

function initDashboardControls() {
    document.getElementById('logout-btn').addEventListener('click', logout);
    document.getElementById('refresh-btn').addEventListener('click', () => {
        loadAnalytics();
        loadReviews();
        resetCountdown();
    });
    
    document.getElementById('rating-filter').addEventListener('change', (e) => {
        state.filters.rating = e.target.value;
        state.currentPage = 1;
        loadReviews();
    });
    let searchTimeout;
    document.getElementById('search-input').addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            state.filters.search = e.target.value;
            state.currentPage = 1;
            loadReviews();
        }, 500);
    });
    document.getElementById('prev-page').addEventListener('click', () => {
        if (state.currentPage > 1) {
            state.currentPage--;
            loadReviews();
        }
    });
    
    document.getElementById('next-page').addEventListener('click', () => {
        if (state.currentPage < state.totalPages) {
            state.currentPage++;
            loadReviews();
        }
    });
}


function startAutoRefresh() {
    state.countdown = 30;
    updateCountdown();
    
    state.refreshTimer = setInterval(() => {
        state.countdown--;
        updateCountdown();
        
        if (state.countdown <= 0) {
            loadAnalytics();
            loadReviews();
            state.countdown = 30;
        }
    }, 1000);
}

function stopAutoRefresh() {
    if (state.refreshTimer) {
        clearInterval(state.refreshTimer);
        state.refreshTimer = null;
    }
}

function resetCountdown() {
    state.countdown = 30;
    updateCountdown();
}

function updateCountdown() {
    document.getElementById('countdown').textContent = state.countdown;
}

async function loadAnalytics() {
    try {
        const response = await fetch(API_ENDPOINTS.analytics, {
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });

        if (response.status === 401) {
            logout();
            return;
        }

        if (!response.ok) {
            throw new Error('Failed to load analytics');
        }

        const data = await response.json();
        state.analytics = data;
        renderAnalytics(data);
        
    } catch (error) {
        console.error('Analytics error:', error);
        showToast('error', 'Failed to load analytics');
    }
}

async function loadReviews() {
    showLoadingState(true);
    
    try {
        const params = new URLSearchParams({
            page: state.currentPage,
            page_size: CONFIG.pageSize
        });
        
        if (state.filters.rating) {
            params.append('rating', state.filters.rating);
        }
        
        if (state.filters.search) {
            params.append('search', state.filters.search);
        }

        const response = await fetch(`${API_ENDPOINTS.reviews}?${params}`, {
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });

        if (response.status === 401) {
            logout();
            return;
        }

        if (!response.ok) {
            throw new Error('Failed to load reviews');
        }

        const data = await response.json();
        state.reviews = data.reviews;
        state.totalPages = Math.ceil(data.total_count / CONFIG.pageSize) || 1;
        
        renderReviews(data.reviews);
        renderPagination(data);
        
    } catch (error) {
        console.error('Reviews error:', error);
        showToast('error', 'Failed to load reviews');
    } finally {
        showLoadingState(false);
    }
}
function renderAnalytics(data) {
    document.getElementById('total-reviews').textContent = data.total_reviews.toLocaleString();
    document.getElementById('avg-rating').textContent = data.average_rating.toFixed(1) + ' ⭐';
    document.getElementById('reviews-today').textContent = data.reviews_today.toLocaleString();
    document.getElementById('reviews-week').textContent = data.reviews_this_week.toLocaleString();
    renderRatingChart(data.rating_distribution);
}

function renderRatingChart(distribution) {
    const ctx = document.getElementById('rating-chart').getContext('2d');
    
    const labels = ['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars'];
    const values = [
        distribution['1'] || 0,
        distribution['2'] || 0,
        distribution['3'] || 0,
        distribution['4'] || 0,
        distribution['5'] || 0
    ];
    const colors = ['#EF4444', '#F97316', '#F59E0B', '#3B82F6', '#10B981'];

    if (ratingChart) {
        ratingChart.destroy();
    }
    
    ratingChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: (context) => `${context.raw} reviews`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function renderReviews(reviews) {
    const tbody = document.getElementById('reviews-tbody');
    const emptyState = document.getElementById('empty-state');
    
    if (reviews.length === 0) {
        tbody.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }
    
    emptyState.style.display = 'none';
    
    tbody.innerHTML = reviews.map(review => `
        <tr onclick="showReviewDetail('${review.id}')">
            <td>
                <span class="rating-badge rating-${review.rating}">
                    ${'⭐'.repeat(review.rating)}
                </span>
            </td>
            <td>
                <div class="review-text">${truncateText(escapeHtml(review.review_text), 100)}</div>
            </td>
            <td>
                <div class="ai-summary">${escapeHtml(review.admin_summary)}</div>
            </td>
            <td>
                <div class="recommended-actions">${escapeHtml(review.recommended_actions)}</div>
            </td>
            <td>
                <span class="time-ago">${formatTimeAgo(review.submission_time)}</span>
            </td>
        </tr>
    `).join('');
}

function renderPagination(data) {
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    const pageInfo = document.getElementById('page-info');
    
    prevBtn.disabled = state.currentPage <= 1;
    nextBtn.disabled = !data.has_more;
    
    pageInfo.textContent = `Page ${state.currentPage} of ${state.totalPages} (${data.total_count} reviews)`;
}

function showLoadingState(loading) {
    const loadingState = document.getElementById('loading-state');
    const tableContainer = document.querySelector('.table-container');
    
    if (loading) {
        loadingState.style.display = 'block';
        tableContainer.style.opacity = '0.5';
    } else {
        loadingState.style.display = 'none';
        tableContainer.style.opacity = '1';
    }
}


function initModal() {
    const modal = document.getElementById('review-modal');
    const backdrop = document.getElementById('modal-backdrop');
    const closeBtn = document.getElementById('modal-close');
    
    backdrop.addEventListener('click', closeModal);
    closeBtn.addEventListener('click', closeModal);
    
    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

function showReviewDetail(reviewId) {
    const review = state.reviews.find(r => r.id === reviewId);
    if (!review) return;
    
    const modalBody = document.getElementById('modal-body');
    
    modalBody.innerHTML = `
        <div class="detail-section">
            <div class="detail-label">Rating</div>
            <div class="detail-value">
                <span class="rating-badge rating-${review.rating}">
                    ${'⭐'.repeat(review.rating)} (${review.rating}/5)
                </span>
            </div>
        </div>
        
        <div class="detail-section">
            <div class="detail-label">Customer Review</div>
            <div class="detail-value review-full">${escapeHtml(review.review_text)}</div>
        </div>
        
        <div class="detail-section">
            <div class="detail-label">AI Response to Customer</div>
            <div class="detail-value">${escapeHtml(review.user_response)}</div>
        </div>
        
        <div class="detail-section">
            <div class="detail-label">AI Summary</div>
            <div class="detail-value">${escapeHtml(review.admin_summary)}</div>
        </div>
        
        <div class="detail-section">
            <div class="detail-label">Recommended Actions</div>
            <div class="detail-value">${escapeHtml(review.recommended_actions)}</div>
        </div>
        
        <div class="detail-section">
            <div class="detail-label">Submitted</div>
            <div class="detail-value">${formatDate(review.submission_time)}</div>
        </div>
    `;
    
    document.getElementById('review-modal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('review-modal').style.display = 'none';
}


function showToast(type, message) {
    const toast = document.getElementById(`${type}-toast`);
    const messageEl = document.getElementById(`${type}-message`);
    
    if (messageEl) {
        messageEl.textContent = message;
    }
    
    toast.style.display = 'flex';
    setTimeout(() => {
        hideToast(`${type}-toast`);
    }, 5000);
}

function hideToast(toastId) {
    document.getElementById(toastId).style.display = 'none';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
}

function formatTimeAgo(dateString) {
    let date;
    if (dateString.includes('T') && !dateString.includes('Z') && !dateString.includes('+')) {
        date = new Date(dateString + 'Z');
    } else {
        date = new Date(dateString);
    }
    
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 0) return 'Just now';
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hr ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`;
    
    return date.toLocaleDateString();
}

function formatDate(dateString) {
    let date;
    if (dateString.includes('T') && !dateString.includes('Z') && !dateString.includes('+')) {
        date = new Date(dateString + 'Z');
    } else {
        date = new Date(dateString);
    }
    
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}
