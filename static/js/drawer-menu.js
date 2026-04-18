const menuIcon = document.getElementById('menu-icon');
const drawerMenu = document.getElementById('drawer-menu');

menuIcon.addEventListener('click', (event) => {
  event.stopPropagation(); // Prevent the click from immediately closing the menu
  drawerMenu.classList.toggle('open');
  updateMenuIcon();
});

// Close the drawer when clicking anywhere outside it
document.addEventListener('click', (event) => {
  if (drawerMenu.classList.contains('open') && !drawerMenu.contains(event.target) && !menuIcon.contains(event.target)) {
    drawerMenu.classList.remove('open');
    updateMenuIcon();
  }
});

// Close the drawer menu when a link is clicked
const drawerLinks = drawerMenu.querySelectorAll('a');
drawerLinks.forEach(link => {
  link.addEventListener('click', () => {
    drawerMenu.classList.remove('open');
    updateMenuIcon();
  });
});

function updateMenuIcon() {
  if (drawerMenu.classList.contains('open')) {
    menuIcon.innerHTML = '<i class="fas fa-times"></i>'; // Cancel icon
  } else {
    menuIcon.innerHTML = '<i class="fas fa-bars"></i>'; // Menu icon
  }
}
