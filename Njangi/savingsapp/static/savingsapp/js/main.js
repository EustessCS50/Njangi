// Minimal JS for future enhancements
console.log('Njangi frontend loaded');

document.addEventListener('DOMContentLoaded', function(){
	const toggle = document.getElementById('navToggle');
	const links = document.getElementById('navLinks');
	if(toggle && links){
		toggle.addEventListener('click', function(){
			links.classList.toggle('show');
		});
	}
});
