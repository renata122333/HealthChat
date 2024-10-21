import { initializeApp } from "https://www.gstatic.com/firebasejs/9.16.0/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/9.16.0/firebase-auth.js";
import { getDatabase, ref, set } from "https://www.gstatic.com/firebasejs/9.16.0/firebase-database.js";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyBly7FZ98gsUsuONbQ6GGiUv08MpF2gizw",
  authDomain: "healthchat-92756.firebaseapp.com",
  projectId: "healthchat-92756",
  storageBucket: "healthchat-92756.appspot.com",
  messagingSenderId: "127172674064",
  appId: "1:127172674064:web:27b2eb8193a7b657f30095",
  databaseURL: "https://healthchat-92756-default-rtdb.firebaseio.com/" // Make sure the URL starts with https://
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const database = getDatabase(app); // Initialize the Realtime Database

// Login Function
window.login = async () => {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
        // Show the loader when login starts
        document.getElementById('loader').style.display = 'flex';

        // Sign in the user
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;

        // Get the user's ID token
        const idToken = await user.getIdToken();

        // Send the ID token to the server for verification
        const response = await fetch('/verify_token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: idToken })
        });

        const data = await response.json();

        // Hide the loader once the process is complete
        document.getElementById('loader').style.display = 'none';

        // Check if the login was successful
        if (data.success) {
            // Redirect to the home page
            window.location.href = '/home';
        } else {
            // Display login failure message
            document.getElementById("error-message").textContent = 'Login failed. Please try again.';
        }
    } catch (error) {
        // Hide the loader in case of an error
        document.getElementById('loader').style.display = 'none';

        // Display error message
        document.getElementById("error-message").textContent = error.message;
    }
};

// Function to toggle password visibility
window.togglePasswordVisibility = () => {
    const passwordInput = document.getElementById("password");
    if (passwordInput.type === "password") {
        passwordInput.type = "text";
    } else {
        passwordInput.type = "password";
    }
};

// Optimized Signup Function
window.signup = async () => {
    try {
        const name = document.getElementById("name").value;
        const surname = document.getElementById("surname").value;
        const dob = document.getElementById("dob").value;
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;
        const description = document.getElementById("description").value;

        // Show the loader when the signup process starts
        document.getElementById('loader').style.display = 'flex';

        // Create user in Firebase Auth
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;

        // Save additional user data in Firebase Realtime Database
        await set(ref(database, 'users/' + user.uid), {
            name: name,
            surname: surname,
            dob: dob,
            email: email,
            profile_picture_url: 'https://placehold.co/100x100',
            description: description
        });

        // Hide the loader once the process is complete
        document.getElementById('loader').style.display = 'none';

        alert('Signup successful!');
        window.location.href = '/';  // Redirect to login page after successful signup
    } catch (error) {
        // Hide the loader in case of an error
        document.getElementById('loader').style.display = 'none';

        // Display error message
        alert(error.message);
    }
};

// Update Profile Function (optional if handling via JS)
window.updateProfile = () => {
    const name = document.getElementById("name").value;
    const surname = document.getElementById("surname").value;
    const dob = document.getElementById("dob").value;
    const email = document.getElementById("email").value;
    const description = document.getElementById("description").value;

    const user = auth.currentUser;
    if (user) {
        update(ref(database, 'users/' + user.uid), {
            name: name,
            surname: surname,
            dob: dob,
            email: email,
            description: description
        }).then(() => {
            alert('Profile updated successfully.');
        }).catch((error) => {
            alert(error.message);
        });
    }
};
