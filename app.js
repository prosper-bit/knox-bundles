document.addEventListener('DOMContentLoaded', () => {
    const welcomeScreen = document.getElementById('welcome-screen');
    const bundleSelectionScreen = document.getElementById('bundle-selection-screen');
    const orderFormScreen = document.getElementById('order-form-screen');
    const confirmationScreen = document.getElementById('confirmation-screen');
    const bundleCardsContainer = document.getElementById('bundle-cards');
    const orderForm = document.getElementById('order-form');

    let selectedBundle = null;

    // --- Screen Transitions ---
    function showScreen(screen) {
        welcomeScreen.style.display = 'none';
        bundleSelectionScreen.style.display = 'none';
        orderFormScreen.style.display = 'none';
        confirmationScreen.style.display = 'none';
        screen.style.display = 'block';
    }

    // --- Welcome Screen ---
    setTimeout(() => {
        showScreen(bundleSelectionScreen);
    }, 2000);

    // --- Fetch and Display Bundles ---
    fetch('bundles.json')
        .then(response => response.json())
        .then(bundles => {
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

    // --- Bundle Selection ---
    bundleCardsContainer.addEventListener('click', (event) => {
        if (event.target.tagName === 'BUTTON') {
            const bundleId = event.target.dataset.bundleId;
            fetch('bundles.json')
                .then(response => response.json())
                .then(bundles => {
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
                bundle: selectedBundle.name,
                price: selectedBundle.price
            };

            // --- Telegram WebApp Integration ---
            try {
                window.Telegram.WebApp.sendData(JSON.stringify(orderData));
                showScreen(confirmationScreen);
            } catch (error) {
                console.error('Error sending data to Telegram:', error);
                // Fallback for testing outside Telegram
                alert('Order submitted (for testing)!' + JSON.stringify(orderData));
                showScreen(confirmationScreen);
            }

        } else {
            alert('Please fill in all fields.');
        }
    });

    // --- Initialize Telegram WebApp ---
    try {
        window.Telegram.WebApp.ready();
        window.Telegram.WebApp.expand();
    } catch (error) {
        console.error('Telegram WebApp SDK not available.');
    }
});
