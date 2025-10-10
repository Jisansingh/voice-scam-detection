const phoneInput = document.getElementById('phoneNumber');
const otpInput = document.getElementById('otp');
const sendOtpBtn = document.getElementById('sendOtpBtn');
const loginBtn = document.getElementById('loginBtn');
const form = document.getElementById('loginForm');
const messageBox = document.getElementById('message');

let generatedOtp = '';
let otpTimeout;

// Format phone number as user types
phoneInput.addEventListener('input', (e) => {
    const value = e.target.value.replace(/\D/g, '');
    if (value.length === 10) {
        sendOtpBtn.disabled = false;
    } else {
        sendOtpBtn.disabled = true;
    }
});

sendOtpBtn.onclick = async () => {
    if (!phoneInput.value.match(/^[0-9]{10}$/)) {
        showMessage('Please enter a valid 10-digit phone number.', true);
        return;
    }

    try {
        // Show loading state
        sendOtpBtn.disabled = true;
        sendOtpBtn.textContent = 'Sending...';

        // Call backend to send OTP
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                phone: phoneInput.value
            })
        });

        const data = await response.json();

        if (data.success && data.otp_sent) {
            showMessage(data.message || 'OTP sent successfully! Check the console for the code.', false);
            otpInput.disabled = false;
            loginBtn.disabled = false;
            otpInput.focus();

            // Start OTP expiry timer
            if (otpTimeout) clearTimeout(otpTimeout);
            otpTimeout = setTimeout(() => {
                otpInput.disabled = true;
                loginBtn.disabled = true;
                showMessage('OTP expired. Please request a new one.', true);
            }, 300000); // 5 minutes

            // Update button for resend
            sendOtpBtn.textContent = 'Resend OTP';
        } else {
            showMessage(data.error || data.message || 'Failed to send OTP. Please try again.', true);
        }
    } catch (error) {
        showMessage('Error sending OTP. Please try again.', true);
    } finally {
        sendOtpBtn.disabled = false;
    }
};

form.onsubmit = async (e) => {
    e.preventDefault();
    
    try {
        loginBtn.disabled = true;
        loginBtn.textContent = 'Logging in...';

        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                phone: phoneInput.value,
                otp: otpInput.value
            })
        });

        const data = await response.json();

        if (data.success) {
            showMessage('Login successful! Redirecting...', false);
            // Redirect to dashboard after successful login
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1500);
        } else {
            showMessage(data.error || data.message || 'Invalid OTP. Please try again.', true);
            loginBtn.disabled = false;
            loginBtn.textContent = 'Login';
        }
    } catch (error) {
        showMessage('Error verifying OTP. Please try again.', true);
        loginBtn.disabled = false;
        loginBtn.textContent = 'Login';
    }
};

function showMessage(msg, isError) {
    messageBox.textContent = msg;
    messageBox.style.color = isError ? "#f05753" : "#30cb89";
    messageBox.style.display = 'block';
}

// Initial state setup
sendOtpBtn.disabled = true;