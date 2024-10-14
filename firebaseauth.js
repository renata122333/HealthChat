import { initializeApp } from "https://www.gstatic.com/firebasejs/9.23.0/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut } from "https://www.gstatic.com/firebasejs/9.23.0/firebase-auth.js";

// Your web app's Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyATBSNccQUICwXJL-3hR5LdSVoLAX513N4",
    authDomain: "heartchat-7268c.firebaseapp.com",
    projectId: "heartchat-7268c",
    storageBucket: "heartchat-7268c.appspot.com",
    messagingSenderId: "55342640146",
    appId: "1:55342640146:web:94f93184b34e2bfb2c3ccb"
  };

 // Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Function to handle user signup
function signUp() {
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    createUserWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {
            const user = userCredential.user;
            console.log("User signed up:", user);
            window.location.href = 'login.html';
        })
        .catch((error) => {
            const errorMessage = error.message;
            console.error("Signup Error:", errorMessage);
            alert(errorMessage);
        });
}

// Function to handle user login
function logIn() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    signInWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {
            const user = userCredential.user;
            console.log("User logged in:", user);
            window.location.href = 'home.html';
        })
        .catch((error) => {
            const errorMessage = error.message;
            console.error("Login Error:", errorMessage);
            alert(errorMessage);
        });
}

// Event listener for signup button
const signupButton = document.getElementById('signup-button');
if (signupButton) {
    signupButton.addEventListener('click', (event) => {
        event.preventDefault();
        signUp();
    });
} else {
    console.error("Signup button not found.");
}

// Event listener for login form submission
const loginForm = document.getElementById('login-form');
if (loginForm) {
    loginForm.addEventListener('submit', (event) => {
        event.preventDefault();
        logIn();
    });
} else {
    console.error("Login form not found.");
}

// Event listener for logout
const logoutButton = document.querySelector('.logout');
if (logoutButton) {
    logoutButton.addEventListener('click', () => {
        signOut(auth).then(() => {
            window.location.href = 'login.html';
        }).catch((error) => {
            console.error("Sign Out Error", error);
        });
    });
} else {
    console.error("Logout button not found.");
}

