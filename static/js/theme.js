// Check for saved theme preference or use the system preference
function getThemePreference() {
    if (localStorage.getItem('theme') === 'dark' || 
        (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        return 'dark';
    }
    return 'light';
}

// Set theme based on preference
function setTheme(theme) {
    if (theme === 'dark') {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
    updateThemeIcons(theme);
}

// Update theme toggle icons
function updateThemeIcons(theme) {
    const sunIcons = document.querySelectorAll('.theme-sun');
    const moonIcons = document.querySelectorAll('.theme-moon');
    
    if (theme === 'dark') {
        sunIcons.forEach(icon => icon.classList.remove('hidden'));
        moonIcons.forEach(icon => icon.classList.add('hidden'));
    } else {
        sunIcons.forEach(icon => icon.classList.add('hidden'));
        moonIcons.forEach(icon => icon.classList.remove('hidden'));
    }
}

// Toggle the theme
function toggleTheme() {
    const currentTheme = localStorage.getItem('theme') || 
        (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    
    // Save theme preference to user account via API if user is logged in
    if (document.body.dataset.userLoggedIn === 'true') {
        fetch('/api/user/theme-preference', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ theme: newTheme })
        }).catch(err => console.error('Failed to save theme preference:', err));
    }
}

// Initialize theme
document.addEventListener('DOMContentLoaded', function() {
    // Set initial theme
    const theme = getThemePreference();
    setTheme(theme);
    
    // Add click event listeners to all theme toggle buttons
    const themeToggles = document.querySelectorAll('.theme-toggle');
    themeToggles.forEach(button => {
        button.addEventListener('click', toggleTheme);
    });
});