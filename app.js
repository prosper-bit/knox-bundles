document.addEventListener('DOMContentLoaded', () => {
    // --- Initialize Telegram WebApp ---
    try {
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.ready();
            window.Telegram.WebApp.expand();
            console.log("Telegram WebApp SDK is ready.");
        } else {
            console.error("Telegram WebApp SDK not found.");
        }
    } catch (error) {
        console.error('Error initializing Telegram WebApp:', error);
    }

    const welcomeScreen = document.getElementById('welcome-screen');
    const networkSelectionScreen = document.getElementById('network-selection-screen');
    const bundleSelectionScreen = document.getElementById('bundle-selection-screen');
    const orderFormScreen = document.getElementById('order-form-screen');
    const confirmationScreen = document.getElementById('confirmation-screen');
    const networkButtons = document.getElementById('network-buttons');
    const bundleCardsContainer = document.getElementById('bundle-cards');
    const orderForm = document.getElementById('order-form');

    let selectedNetwork = null;
    let selectedBundle = null;

    // --- Screen Transitions ---
    function showScreen(screen) {
        welcomeScreen.style.display = 'none';
        networkSelectionScreen.style.display = 'none';
        bundleSelectionScreen.style.display = 'none';
        orderFormScreen.style.display = 'none';
        confirmationScreen.style.display = 'none';
        screen.style.display = 'block';
    }

    // --- Welcome Screen ---
    setTimeout(() => {
        showScreen(networkSelectionScreen);
    }, 2000);

    // --- Network Selection ---
    networkButtons.addEventListener('click', (event) => {
        if (event.target.classList.contains('network-btn')) {
            selectedNetwork = event.target.dataset.network;
            displayBundles(selectedNetwork);
            showScreen(bundleSelectionScreen);
        }
    });

    // --- Fetch and Display Bundles ---
    function displayBundles(network) {
        bundleCardsContainer.innerHTML = ''; // Clear existing bundles
        fetch('bundles.json')
            .then(response => response.json())
            .then(data => {
                const bundles = data[network];
                bundles.forEach(bundle => {
                    const card = document.createElement('div');
                    card.className = 'bundle-card';
                    card.innerHTML = `
                        <h3>${bundle.name}</h3>
                        <p>${bundle.description}</p>
                        <p class="price">${bundle.price}</p>
                        <button data-bundle-id="${bundle.id}">Select</button>
                    `;
                    bundleCardsContainer.appendChild(card);
                });
            });
    }

    // --- Bundle Selection ---
    bundleCardsContainer.addEventListener('click', (event) => {
        if (event.target.tagName === 'BUTTON') {
            const bundleId = event.target.dataset.bundleId;
            fetch('bundles.json')
                .then(response => response.json())
                .then(data => {
                    const bundles = data[selectedNetwork];
                    selectedBundle = bundles.find(b => b.id == bundleId);
                    showScreen(orderFormScreen);
                });
        }
    });

    // --- Order Form Submission ---
    orderForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const name = document.getElementById('name').value;
        const contact = document.getElementById('contact').value;

        if (name && contact) {
            const orderData = {
                name: name,
                contact: contact,
                network: selectedNetwork,
                bundle: selectedBundle.name,
                price: selectedBundle.price
            };

            // --- Telegram WebApp Integration ---
            try {
                if (window.Telegram && window.Telegram.WebApp) {
                    window.Telegram.WebApp.sendData(JSON.stringify(orderData));
                    // The confirmation screen will only be shown if sendData is successful.
                    // In a real scenario, you might wait for a response from the bot.
                    showScreen(confirmationScreen);
                } else {
                    console.error("Telegram WebApp SDK is not available. Cannot send data.");
                    alert('Order submitted (for testing outside Telegram)!');
                    showScreen(confirmationScreen);
                }
            } catch (error) {
                console.error('Error sending data to Telegram:', error);
                alert('An error occurred while submitting your order.');
            }

        } else {
            alert('Please fill in all fields.');
        }
    });
});
