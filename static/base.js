/*=========================================================
    STYRIVA
    Premium Base JavaScript
    Part 1/3
=========================================================*/

"use strict";

/*=========================================================
    DOM READY
=========================================================*/

document.addEventListener("DOMContentLoaded", () => {

    initializeMobileMenu();
    initializeNavbar();
    initializeAlerts();
    initializeRevealAnimations();
    initializeSmoothScroll();
    initializeLoadingButtons();

});


/*=========================================================
    MOBILE MENU
=========================================================*/

function initializeMobileMenu() {

    const button = document.getElementById("menuButton");

    const menu = document.getElementById("mobileMenu");

    if (!button || !menu) return;

    const icon = button.querySelector("i");

    button.addEventListener("click", () => {

        menu.classList.toggle("show");

        if (menu.classList.contains("show")) {

            icon.classList.remove("fa-bars");
            icon.classList.add("fa-xmark");

            document.body.style.overflow = "hidden";

        }

        else{

            icon.classList.remove("fa-xmark");
            icon.classList.add("fa-bars");

            document.body.style.overflow = "";

        }

    });


    menu.querySelectorAll("a").forEach(link => {

        link.addEventListener("click", () => {

            menu.classList.remove("show");

            icon.classList.remove("fa-xmark");

            icon.classList.add("fa-bars");

            document.body.style.overflow = "";

        });

    });

}


/*=========================================================
    NAVBAR EFFECT
=========================================================*/

function initializeNavbar(){

    const navbar=document.querySelector(".navbar");

    if(!navbar) return;

    window.addEventListener("scroll",()=>{

        if(window.scrollY>20){

            navbar.style.background="rgba(5,5,5,.95)";

            navbar.style.backdropFilter="blur(28px)";

            navbar.style.boxShadow="0 15px 40px rgba(0,0,0,.45)";

        }

        else{

            navbar.style.background="rgba(5,5,5,.70)";

            navbar.style.boxShadow="none";

        }

    });

}


/*=========================================================
    AUTO HIDE ALERTS
=========================================================*/

function initializeAlerts(){

    const alerts=document.querySelectorAll(".alert");

    if(!alerts.length) return;

    setTimeout(()=>{

        alerts.forEach(alert=>{

            alert.style.transition=".45s";

            alert.style.opacity="0";

            alert.style.transform="translateY(-15px)";

            setTimeout(()=>{

                alert.remove();

            },500);

        });

    },4500);

}


/*=========================================================
    SCROLL REVEAL
=========================================================*/

function initializeRevealAnimations(){

    const elements=document.querySelectorAll(".fade-up");

    if(!elements.length) return;

    const observer=new IntersectionObserver(

        entries=>{

            entries.forEach(entry=>{

                if(entry.isIntersecting){

                    entry.target.classList.add("visible");

                }

            });

        },

        {

            threshold:.15

        }

    );

    elements.forEach(element=>{

        observer.observe(element);

    });

}


/*=========================================================
    RIPPLE BUTTON EFFECT
=========================================================*/

function createRipple(event){

    const button = event.currentTarget;

    const circle = document.createElement("span");

    const diameter = Math.max(

        button.clientWidth,

        button.clientHeight

    );

    const radius = diameter / 2;

    const rect = button.getBoundingClientRect();

    circle.style.width = circle.style.height = `${diameter}px`;

    circle.style.left = `${event.clientX - rect.left - radius}px`;

    circle.style.top = `${event.clientY - rect.top - radius}px`;

    circle.classList.add("ripple");

    const existing = button.querySelector(".ripple");

    if(existing){

        existing.remove();

    }

    button.appendChild(circle);

}

document.querySelectorAll("button").forEach(button=>{

    button.addEventListener("click",createRipple);

});


/*=========================================================
    LOADING BUTTONS
=========================================================*/

function initializeLoadingButtons(){

    document.querySelectorAll("form").forEach(form=>{

        form.addEventListener("submit",()=>{

            const button=form.querySelector(

                "button[type='submit']"

            );

            if(!button) return;

            if(button.disabled) return;

            button.disabled=true;

            button.dataset.original=button.innerHTML;

            button.innerHTML=`

                <i class="fa-solid fa-spinner fa-spin"></i>

                Please wait...

            `;

        });

    });

}


/*=========================================================
    SMOOTH SCROLL
=========================================================*/

function initializeSmoothScroll(){

    document.querySelectorAll('a[href^="#"]').forEach(link=>{

        link.addEventListener("click",function(e){

            const target=document.querySelector(

                this.getAttribute("href")

            );

            if(!target) return;

            e.preventDefault();

            target.scrollIntoView({

                behavior:"smooth",

                block:"start"

            });

        });

    });

}


/*=========================================================
    PAGE FADE-IN
=========================================================*/

window.addEventListener("load",()=>{

    document.body.style.opacity="1";

});


/*=========================================================
    BACK TO TOP
=========================================================*/

const backToTop=document.getElementById(

    "backToTop"

);

if(backToTop){

    window.addEventListener("scroll",()=>{

        if(window.scrollY>450){

            backToTop.classList.add("show");

        }

        else{

            backToTop.classList.remove("show");

        }

    });

    backToTop.addEventListener("click",()=>{

        window.scrollTo({

            top:0,

            behavior:"smooth"

        });

    });

}


/*=========================================================
    CLOSE MOBILE MENU ON RESIZE
=========================================================*/

window.addEventListener("resize",()=>{

    if(window.innerWidth>900){

        const menu=document.getElementById(

            "mobileMenu"

        );

        const button=document.getElementById(

            "menuButton"

        );

        if(menu){

            menu.classList.remove("show");

        }

        if(button){

            const icon=button.querySelector("i");

            if(icon){

                icon.classList.remove("fa-xmark");

                icon.classList.add("fa-bars");

            }

        }

        document.body.style.overflow="";

    }

});


/*=========================================================
    CONSOLE MESSAGE
=========================================================*/

console.log(

    "%c✨ STYRIVA Loaded Successfully",

    "color:#d4af37;font-size:16px;font-weight:bold;"

);


/*=========================================================
    STYRIVA
    Premium Base JavaScript
    Part 3/3
=========================================================*/


/*=========================================================
    ACTIVE NAVIGATION
=========================================================*/

(function () {

    const current = window.location.pathname;

    document.querySelectorAll(".desktop-nav a, .mobile-menu a").forEach(link => {

        try{

            const url = new URL(link.href);

            if(url.pathname === current){

                link.classList.add("active");

            }

        }

        catch(error){}

    });

})();


/*=========================================================
    ESC CLOSES MOBILE MENU
=========================================================*/

document.addEventListener("keydown", event => {

    if(event.key !== "Escape") return;

    const menu = document.getElementById("mobileMenu");

    const button = document.getElementById("menuButton");

    if(!menu || !button) return;

    menu.classList.remove("show");

    const icon = button.querySelector("i");

    if(icon){

        icon.classList.remove("fa-xmark");

        icon.classList.add("fa-bars");

    }

    document.body.style.overflow = "";

});


/*=========================================================
    IMAGE FADE-IN
=========================================================*/

document.querySelectorAll("img").forEach(image=>{

    if(image.complete){

        image.classList.add("loaded");

    }

    else{

        image.addEventListener("load",()=>{

            image.classList.add("loaded");

        });

    }

});


/*=========================================================
    CARD HOVER EFFECT
=========================================================*/

document.querySelectorAll(".card").forEach(card=>{

    card.addEventListener("mouseenter",()=>{

        card.style.transform="translateY(-8px)";

    });

    card.addEventListener("mouseleave",()=>{

        card.style.transform="translateY(0)";

    });

});


/*=========================================================
    THROTTLE
=========================================================*/

function throttle(callback, delay){

    let waiting = false;

    return (...args)=>{

        if(waiting) return;

        callback(...args);

        waiting = true;

        setTimeout(()=>{

            waiting = false;

        }, delay);

    };

}


/*=========================================================
    WINDOW SCROLL OPTIMIZATION
=========================================================*/

window.addEventListener(

    "scroll",

    throttle(()=>{

        document.documentElement.style.setProperty(

            "--scrollY",

            window.scrollY

        );

    },16)

);


/*=========================================================
    SAFE QUERY HELPER
=========================================================*/

function $(selector){

    return document.querySelector(selector);

}

function $all(selector){

    return document.querySelectorAll(selector);

}


/*=========================================================
    DISABLE DOUBLE SUBMIT
=========================================================*/

document.querySelectorAll("form").forEach(form=>{

    form.addEventListener("keydown",event=>{

        if(event.key==="Enter"){

            const active=document.activeElement;

            if(active && active.tagName==="TEXTAREA"){

                return;

            }

        }

    });

});


/*=========================================================
    PREFERRED REDUCED MOTION
=========================================================*/

if(

    window.matchMedia(

        "(prefers-reduced-motion: reduce)"

    ).matches

){

    document.documentElement.style.scrollBehavior="auto";

}


/*=========================================================
    GLOBAL ERROR LOGGER
=========================================================*/

window.addEventListener("error",event=>{

    console.error(

        "STYRIVA Error:",

        event.message

    );

});


/*=========================================================
    PERFORMANCE LOG
=========================================================*/

window.addEventListener("load",()=>{

    const time = performance.now();

    console.log(

        `%cSTYRIVA Ready ⚡ ${Math.round(time)} ms`,

        "color:#d4af37;font-size:14px;font-weight:bold"

    );

});


/*=========================================================
    END OF FILE
=========================================================*/