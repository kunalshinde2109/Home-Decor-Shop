/* =====================================================
   CASA AURA — INTERACTIONS
   ===================================================== */


/* ================= MOBILE MENU ================= */

const menuBtn = document.getElementById("menuBtn");
const mobileMenu = document.getElementById("mobileMenu");
const closeMenu = document.getElementById("closeMenu");

if (menuBtn && mobileMenu) {

    menuBtn.addEventListener("click", () => {
        mobileMenu.classList.add("active");
        document.body.style.overflow = "hidden";
    });

}

if (closeMenu && mobileMenu) {

    closeMenu.addEventListener("click", () => {
        mobileMenu.classList.remove("active");
        document.body.style.overflow = "";
    });

}


/* Close menu when navigation link clicked */

document.querySelectorAll(".mobile-menu a").forEach(link => {

    link.addEventListener("click", () => {

        mobileMenu.classList.remove("active");

        document.body.style.overflow = "";

    });

});


/* ================= NAVBAR SCROLL ================= */

const navbar = document.querySelector(".navbar");

window.addEventListener(
    "scroll",
    () => {

        if (window.scrollY > 40) {

            navbar.classList.add("scrolled");

        } else {

            navbar.classList.remove("scrolled");

        }

    },
    {
        passive: true
    }
);


/* ================= SCROLL REVEAL ================= */

const revealElements =
    document.querySelectorAll(".reveal");

const revealObserver =
    new IntersectionObserver(
        (entries, observer) => {

            entries.forEach(entry => {

                if (entry.isIntersecting) {

                    entry.target.classList.add("visible");

                    observer.unobserve(entry.target);

                }

            });

        },
        {
            threshold: 0.12,
            rootMargin: "0px 0px -40px 0px"
        }
    );


revealElements.forEach(element => {

    revealObserver.observe(element);

});


/* ================= CART DEMO ================= */

const addButtons =
    document.querySelectorAll(".add-btn");

const cartCount =
    document.querySelector(".cart-count");

let cartItems = 0;


addButtons.forEach(button => {

    button.addEventListener("click", () => {

        cartItems++;

        if (cartCount) {
            cartCount.textContent = cartItems;
        }

        button.textContent = "Added ✓";

        button.style.transform = "scale(0.95)";

        setTimeout(() => {

            button.style.transform = "";

        }, 150);

        setTimeout(() => {

            button.textContent = "Add +";

        }, 1200);

    });

});


/* ================= WISHLIST ================= */




/* ================= IMAGE LOAD EFFECT ================= */

document.querySelectorAll("img").forEach(image => {

    image.addEventListener("load", () => {

        image.classList.add("loaded");

    });

});


/* ================= ESC KEY ================= */

document.addEventListener("keydown", event => {

    if (event.key === "Escape") {

        if (mobileMenu) {

            mobileMenu.classList.remove("active");

            document.body.style.overflow = "";

        }

    }

});