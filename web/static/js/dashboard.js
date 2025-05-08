/**
 * VidID Admin Dashboard
 * Main JavaScript file for the admin dashboard functionality
 */

// Initialize the dashboard when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

/**
 * Initialize the dashboard components
 */
function initializeDashboard() {
    // Initialize active navigation link
    highlightActiveNavLink();
    
    // Initialize charts if they exist on the page
    initializeCharts();
    
    // Initialize data refresh functionality
    initializeDataRefresh();
    
    // Initialize any date range pickers
    initializeDateRangePickers();
    
    console.log('Dashboard initialized successfully');
}

/**
 * Highlight the active navigation link based on current URL
 */
function highlightActiveNavLink() {
    // Get current path
    const currentPath = window.location.pathname;
    
    // Find all navigation links
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    
    // Iterate through links and add 'active' class to matching path
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

/**
 * Initialize chart.js charts on the dashboard
 */
function initializeCharts() {
    // Find all chart canvases
    const chartCanvases = document.querySelectorAll('[data-chart]');
    
    // Initialize each chart with its configuration
    chartCanvases.forEach(canvas => {
        const chartType = canvas.getAttribute('data-chart');
        const chartId = canvas.id;
        
        switch(chartType) {
            case 'ingestion':
                initializeIngestionChart(chartId);
                break;
            case 'performance':
                initializePerformanceChart(chartId);
                break;
            case 'users':
                initializeUsersChart(chartId);
                break;
            case 'queries':
                initializeQueriesChart(chartId);
                break;
            case 'resources':
                initializeResourcesChart(chartId);
                break;
            default:
                console.warn(`Unknown chart type: ${chartType}`);
        }
    });
}

/**
 * Initialize content ingestion chart
 */
function initializeIngestionChart(chartId) {
    const ctx = document.getElementById(chartId).getContext('2d');
    
    // This would normally load data from an API
    // For demonstration, using placeholder data
    const data = {
        labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'],
        datasets: [
            {
                label: 'Streaming',
                data: [65, 59, 80, 81, 56, 55, 40],
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderColor: 'rgb(255, 99, 132)',
                borderWidth: 1
            },
            {
                label: 'Television',
                data: [28, 48, 40, 19, 86, 27, 90],
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgb(54, 162, 235)',
                borderWidth: 1
            },
            {
                label: 'YouTube',
                data: [45, 25, 30, 52, 48, 63, 57],
                backgroundColor: 'rgba(255, 206, 86, 0.2)',
                borderColor: 'rgb(255, 206, 86)',
                borderWidth: 1
            }
        ]
    };
    
    new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Videos Ingested'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            }
        }
    });
}

/**
 * Initialize system performance chart
 */
function initializePerformanceChart(chartId) {
    const ctx = document.getElementById(chartId).getContext('2d');
    
    // This would normally load data from an API
    // For demonstration, using placeholder data
    const data = {
        labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'],
        datasets: [
            {
                label: 'Avg. Response Time (ms)',
                data: [120, 125, 118, 130, 142, 135, 115],
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgb(75, 192, 192)',
                borderWidth: 1,
                yAxisID: 'y'
            },
            {
                label: 'Query Volume',
                data: [500, 620, 740, 850, 690, 580, 630],
                backgroundColor: 'rgba(153, 102, 255, 0.2)',
                borderColor: 'rgb(153, 102, 255)',
                borderWidth: 1,
                yAxisID: 'y1',
                type: 'line',
                fill: false
            }
        ]
    };
    
    new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Response Time (ms)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: {
                        drawOnChartArea: false
                    },
                    title: {
                        display: true,
                        text: 'Query Volume'
                    }
                }
            }
        }
    });
}

/**
 * Initialize users chart
 */
function initializeUsersChart(chartId) {
    const ctx = document.getElementById(chartId).getContext('2d');
    
    // This would normally load data from an API
    // For demonstration, using placeholder data
    const data = {
        labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        datasets: [{
            label: 'New Users',
            data: [120, 190, 210, 250],
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgb(54, 162, 235)',
            borderWidth: 1
        }, {
            label: 'Active Users',
            data: [450, 520, 580, 650],
            backgroundColor: 'rgba(255, 159, 64, 0.2)',
            borderColor: 'rgb(255, 159, 64)',
            borderWidth: 1
        }]
    };
    
    new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Users'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Time Period'
                    }
                }
            }
        }
    });
}

/**
 * Initialize queries chart
 */
function initializeQueriesChart(chartId) {
    const ctx = document.getElementById(chartId).getContext('2d');
    
    // This would normally load data from an API
    // For demonstration, using placeholder data
    const data = {
        labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
        datasets: [{
            label: 'Queries',
            data: [120, 80, 350, 490, 520, 380],
            backgroundColor: 'rgba(153, 102, 255, 0.2)',
            borderColor: 'rgb(153, 102, 255)',
            borderWidth: 1,
            fill: true
        }]
    };
    
    new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Query Count'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Time of Day'
                    }
                }
            }
        }
    });
}

/**
 * Initialize resources usage chart
 */
function initializeResourcesChart(chartId) {
    const ctx = document.getElementById(chartId).getContext('2d');
    
    // This would normally load data from an API
    // For demonstration, using placeholder data
    const data = {
        labels: ['CPU', 'Memory', 'Disk', 'Network'],
        datasets: [{
            label: 'Resource Usage (%)',
            data: [35, 65, 48, 28],
            backgroundColor: [
                'rgba(255, 99, 132, 0.2)',
                'rgba(54, 162, 235, 0.2)',
                'rgba(255, 206, 86, 0.2)',
                'rgba(75, 192, 192, 0.2)'
            ],
            borderColor: [
                'rgb(255, 99, 132)',
                'rgb(54, 162, 235)',
                'rgb(255, 206, 86)',
                'rgb(75, 192, 192)'
            ],
            borderWidth: 1
        }]
    };
    
    new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Usage (%)'
                    }
                }
            }
        }
    });
}

/**
 * Initialize data refresh functionality
 */
function initializeDataRefresh() {
    // Find all refresh buttons
    const refreshButtons = document.querySelectorAll('[data-refresh]');
    
    // Add click event to each refresh button
    refreshButtons.forEach(button => {
        button.addEventListener('click', function() {
            const target = this.getAttribute('data-refresh');
            refreshData(target);
        });
    });
    
    // Set up auto-refresh if enabled
    const autoRefreshElements = document.querySelectorAll('[data-auto-refresh]');
    autoRefreshElements.forEach(element => {
        const interval = parseInt(element.getAttribute('data-auto-refresh')) || 60000; // Default to 1 minute
        const target = element.getAttribute('data-refresh');
        
        setInterval(() => {
            refreshData(target);
        }, interval);
    });
}

/**
 * Refresh data for a specific component
 */
function refreshData(target) {
    console.log(`Refreshing data for: ${target}`);
    
    // Add loading state
    const targetElement = document.getElementById(target);
    if (targetElement) {
        targetElement.classList.add('loading');
    }
    
    // This would normally make an API call to fetch fresh data
    // For demonstration, just simulate a delay
    setTimeout(() => {
        // Remove loading state
        if (targetElement) {
            targetElement.classList.remove('loading');
        }
        
        console.log(`Data refreshed for: ${target}`);
    }, 1000);
}

/**
 * Initialize date range pickers
 */
function initializeDateRangePickers() {
    // This would normally initialize date pickers with a library like daterangepicker
    // For this example, we'll just log that it would be initialized
    const dateRangePickers = document.querySelectorAll('[data-date-range-picker]');
    if (dateRangePickers.length > 0) {
        console.log(`${dateRangePickers.length} date range pickers would be initialized`);
    }
}

/**
 * Fetch data from the API
 */
async function fetchFromApi(endpoint, params = {}) {
    try {
        // Convert params to query string
        const queryString = Object.keys(params)
            .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
            .join('&');
        
        const url = `/api/${endpoint}${queryString ? `?${queryString}` : ''}`;
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`API request failed with status ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error fetching from API:', error);
        return null;
    }
}
