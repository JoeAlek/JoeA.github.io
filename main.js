// Main JavaScript for JoeA Discord Bot Website

document.addEventListener('DOMContentLoaded', function() {
  // Initialize tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Smooth scrolling for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      
      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        targetElement.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });

  // Animation on scroll
  const animatedElements = document.querySelectorAll('.animate-on-scroll');
  
  if (animatedElements.length > 0) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-in');
        }
      });
    }, { threshold: 0.1 });
    
    animatedElements.forEach(element => {
      observer.observe(element);
    });
  }

  // Mobile menu toggle
  const navbarToggler = document.querySelector('.navbar-toggler');
  const navbarCollapse = document.querySelector('.navbar-collapse');
  
  if (navbarToggler && navbarCollapse) {
    navbarToggler.addEventListener('click', function() {
      navbarCollapse.classList.toggle('show');
    });
  }

  // Copy command to clipboard functionality
  const commandElements = document.querySelectorAll('.copy-command');
  
  commandElements.forEach(element => {
    element.addEventListener('click', function() {
      const commandText = this.querySelector('code').innerText;
      navigator.clipboard.writeText(commandText).then(() => {
        // Show success tooltip or notification
        const originalText = this.querySelector('.copy-icon').innerHTML;
        this.querySelector('.copy-icon').innerHTML = '<i class="fas fa-check"></i>';
        
        setTimeout(() => {
          this.querySelector('.copy-icon').innerHTML = originalText;
        }, 2000);
      }).catch(err => {
        console.error('Could not copy text: ', err);
      });
    });
  });

  // Status indicator update
  const statusIndicator = document.querySelector('.status-indicator');
  
  if (statusIndicator) {
    fetch('/status')
      .then(response => response.json())
      .then(data => {
        if (data.status === 'online') {
          statusIndicator.classList.add('text-success');
          statusIndicator.innerHTML = '<i class="fas fa-circle"></i> Online';
        } else {
          statusIndicator.classList.add('text-warning');
          statusIndicator.innerHTML = '<i class="fas fa-circle"></i> ' + data.status;
        }
      })
      .catch(error => {
        statusIndicator.classList.add('text-danger');
        statusIndicator.innerHTML = '<i class="fas fa-circle"></i> Error';
        console.error('Error fetching status:', error);
      });
  }
});