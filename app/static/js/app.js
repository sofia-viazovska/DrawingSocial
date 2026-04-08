let token = null;
let userEmail = null;
try {
    token = localStorage.getItem('token');
    userEmail = localStorage.getItem('email');
} catch (e) {
    console.warn('LocalStorage is not accessible:', e);
}
let currentDrawingId = null;

function handleSearch(e) {
    if (e) e.preventDefault();
    const input = document.getElementById('search-input');
    if (!input) {
        console.error('search-input not found');
        return;
    }
    const q = input.value.trim();
    console.log('Searching for:', q);
    if (q) {
        window.location.href = `/search?q=${encodeURIComponent(q)}`;
    }
}

// Canvas drawing logic
function setupCanvas(canvasId, colorId, sizeId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let drawing = false;

    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mouseout', stopDrawing);

    // Touch support
    canvas.addEventListener('touchstart', (e) => {
        e.preventDefault();
        const touch = e.touches[0];
        const mouseEvent = new MouseEvent('mousedown', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        canvas.dispatchEvent(mouseEvent);
    }, { passive: false });

    canvas.addEventListener('touchmove', (e) => {
        e.preventDefault();
        const touch = e.touches[0];
        const mouseEvent = new MouseEvent('mousemove', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        canvas.dispatchEvent(mouseEvent);
    }, { passive: false });

    canvas.addEventListener('touchend', (e) => {
        const mouseEvent = new MouseEvent('mouseup', {});
        canvas.dispatchEvent(mouseEvent);
    }, { passive: false });

    function startDrawing(e) {
        drawing = true;
        ctx.beginPath();
        const rect = canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left) * (canvas.width / rect.width);
        const y = (e.clientY - rect.top) * (canvas.height / rect.height);
        ctx.moveTo(x, y);
    }

    function draw(e) {
        if (!drawing) return;
        const rect = canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left) * (canvas.width / rect.width);
        const y = (e.clientY - rect.top) * (canvas.height / rect.height);

        ctx.lineWidth = document.getElementById(sizeId).value;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.strokeStyle = document.getElementById(colorId).value;

        ctx.lineTo(x, y);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(x, y);
    }

    function stopDrawing() {
        drawing = false;
        ctx.beginPath();
    }
}

function clearCanvas(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

function showStatus(msg, isError = false) {
    const el = document.getElementById('status-msg');
    if (!el) return;
    el.innerText = msg;
    el.className = isError ? 'error' : 'success';
    el.classList.remove('hidden');
    setTimeout(() => el.classList.add('hidden'), 3000);
}

async function register() {
    const email = document.getElementById('reg-email').value;
    const nickname = document.getElementById('reg-nickname').value;
    const password = document.getElementById('reg-password').value;
    try {
        const res = await fetch('/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, nickname, password })
        });
        const data = await res.json();
        if (res.ok) {
            showStatus('Реєстрація успішна! Тепер увійдіть.');
            setTimeout(() => window.location.href = '/login', 2000);
        } else {
            showStatus(data.detail || 'Помилка реєстрації', true);
        }
    } catch (e) { showStatus('Помилка з\'єднання', true); }
}

async function login() {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    try {
        const res = await fetch(`/auth/login`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (res.ok) {
            token = data.access_token;
            // Get user info to store correct email/nickname
            const meRes = await fetch('/auth/me', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (meRes.ok) {
                const me = await meRes.json();
                userEmail = me.email;
                try {
                    localStorage.setItem('email', userEmail);
                    localStorage.setItem('token', token);
                } catch (e) {
                    console.error('Failed to save to localStorage:', e);
                }
            }
            showStatus('Вхід виконано!');
            setTimeout(() => window.location.href = '/', 1000);
        } else {
            showStatus(data.detail || 'Невірний логін або пароль', true);
        }
    } catch (e) { showStatus('Помилка з\'єднання', true); }
}

function logout() {
    try {
        localStorage.removeItem('token');
        localStorage.removeItem('email');
    } catch (e) {
        console.error('Failed to clear localStorage:', e);
    }
    token = null;
    window.location.href = '/login';
}

async function saveNewDrawing() {
    const title = document.getElementById('draw-title').value;
    const canvas = document.getElementById('create-canvas');
    const first_layer_data = canvas.toDataURL(); // base64 PNG

    if (!title) return showStatus('Введіть назву', true);

    if (!token) {
        showStatus('Будь ласка, увійдіть', true);
        setTimeout(() => window.location.href = '/login', 1500);
        return;
    }

    try {
        const res = await fetch('/drawings/', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ title, first_layer_data })
        });
        if (res.ok) {
            showStatus('Малюнок створено!');
            document.getElementById('draw-title').value = '';
            setTimeout(() => window.location.href = '/', 1000);
        } else if (res.status === 401) {
            logout();
        } else {
            const data = await res.json();
            showStatus(data.detail || 'Помилка створення', true);
        }
    } catch (e) { showStatus('Помилка з\'єднання', true); }
}

async function openEdit(drawingId, title) {
    window.location.href = `/drawing/${drawingId}`;
}

async function saveLayer() {
    const canvas = document.getElementById('edit-canvas');
    const image_data = canvas.toDataURL();

    if (!token) {
        showStatus('Будь ласка, увійдіть', true);
        setTimeout(() => window.location.href = '/login', 1500);
        return;
    }

    try {
        const res = await fetch(`/drawings/${currentDrawingId}/layers`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ image_data })
        });
        if (res.ok) {
            showStatus('Шар додано!');
            setTimeout(() => window.location.href = '/', 1000);
        } else if (res.status === 401) {
            logout();
        } else {
            const data = await res.json();
            showStatus(data.detail || 'Помилка', true);
        }
    } catch (e) { showStatus('Помилка з\'єднання', true); }
}

async function likeDrawing(drawingId, btn) {
    if (btn) {
        btn.classList.add('animate-pop');
        setTimeout(() => btn.classList.remove('animate-pop'), 300);
    }
    try {
        const res = await fetch(`/drawings/${drawingId}/like`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            showStatus('Лайк поставлено!');
            const q = document.getElementById('search-input')?.value;
            loadFeed(q);
        } else {
            const data = await res.json();
            showStatus(data.detail || 'Помилка', true);
        }
    } catch (e) { showStatus('Помилка з\'єднання', true); }
}


async function renderDrawings(drawings, containerId) {
    const list = document.getElementById(containerId);
    if (!list) return;
    list.innerHTML = '';

    if (drawings.length === 0) {
        list.innerHTML = '<p style="text-align: center; color: #888;">Нічого не знайдено.</p>';
        return;
    }

    for (let d of drawings) {
        const dRes = await fetch(`/drawings/${d.id}`);
        const details = await dRes.json();
        
        const card = document.createElement('div');
        card.className = 'drawing-card';
        
        // Identify collaborators (unique authors of layers other than the owner)
        const collaborators = [];
        const seenIds = new Set([details.owner_id]);
        
        details.layers.forEach(layer => {
            if (!seenIds.has(layer.author_id)) {
                collaborators.push({
                    id: layer.author_id,
                    nickname: layer.author_nickname || 'Анонім'
                });
                seenIds.add(layer.author_id);
            }
        });

        const collaboratorsHtml = collaborators.length > 0 
            ? ` • Співавтори: ${collaborators.map(c => `<a href="/profile/${c.id}" style="color: var(--primary); text-decoration: none; font-weight: bold;">${c.nickname}</a>`).join(', ')}`
            : '';

        card.innerHTML = `
            <div class="flex justify-between items-center">
                <h3>${details.title}</h3>
                <span style="background: var(--primary); padding: 5px 15px; border-radius: 20px; color: white; font-weight: bold; box-shadow: var(--glow);">❤️ ${details.likes_count}</span>
            </div>
            <div class="muted" style="margin-bottom: 15px;">Автор: <a href="/profile/${details.owner_id}" style="color: var(--primary); text-decoration: none; font-weight: bold;">${details.owner_nickname || details.owner_email || 'Анонім'}</a>${collaboratorsHtml} • ${new Date(details.created_at).toLocaleString()}</div>
            
            <div class="drawing-canvas-container" id="display-${details.id}">
                <!-- Layers will be rendered here -->
            </div>

            <div style="margin-top: 20px; display: flex; gap: 12px;">
                <button onclick="likeDrawing(${details.id}, this)" class="secondary" style="flex: 1;">👍 Лайк</button>
                <button onclick="openEdit(${details.id}, '${details.title}')" style="flex: 2;">🎨 Додати свій шар</button>
            </div>
        `;
        list.appendChild(card);

        const display = document.getElementById(`display-${details.id}`);
        const mainCanvas = document.createElement('canvas');
        mainCanvas.width = 500;
        mainCanvas.height = 500;
        mainCanvas.style.width = '100%';
        mainCanvas.style.height = 'auto';
        display.appendChild(mainCanvas);
        const ctx = mainCanvas.getContext('2d');

        for (let layer of details.layers) {
            await new Promise((resolve) => {
                const img = new Image();
                img.crossOrigin = "anonymous";
                img.onload = () => {
                    ctx.drawImage(img, 0, 0, 500, 500);
                    resolve();
                };
                img.src = layer.image_data;
            });
        }
    }
}

async function toggleFollowInSearch(userId, isFollowing, btn) {
    const method = isFollowing ? 'DELETE' : 'POST';
    const action = isFollowing ? 'unfollow' : 'follow';
    
    try {
        const res = await fetch(`/drawings/users/${userId}/${action}`, {
            method: method,
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            showStatus(isFollowing ? 'Ви відписалися' : 'Ви підписалися');
            const newIsFollowing = !isFollowing;
            btn.innerText = newIsFollowing ? 'Відписатися' : 'Підписатися';
            btn.className = newIsFollowing ? 'secondary' : '';
            btn.onclick = (e) => {
                e.stopPropagation();
                toggleFollowInSearch(userId, newIsFollowing, btn);
            };
        } else {
            const data = await res.json();
            showStatus(data.detail || 'Помилка', true);
        }
    } catch (e) {
        showStatus('Помилка з\'єднання', true);
    }
}

async function loadSearchResults(q) {
    const usersList = document.getElementById('users-list');
    const drawingsList = document.getElementById('drawings-list');
    
    try {
        const res = await fetch(`/drawings/search?q=${encodeURIComponent(q)}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.status === 401) return logout();
        const results = await res.json();

        // Render Users
        usersList.innerHTML = '';
        if (results.users.length === 0) {
            usersList.innerHTML = '<p class="muted">Користувачів не знайдено.</p>';
        } else {
            const meRes = await fetch('/auth/me', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const me = await meRes.json();
            const myId = me.id;

            for (const user of results.users) {
                const userCard = document.createElement('div');
                userCard.className = 'user-search-card';
                
                const followRes = await fetch(`/drawings/users/${user.id}/is_following`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const { is_following } = await followRes.json();

                userCard.innerHTML = `
                    <div class="user-info" onclick="window.location.href = '/profile/${user.id}'" style="cursor: pointer;">
                        <div class="user-avatar">${user.nickname[0].toUpperCase()}</div>
                        <div>
                            <div class="user-nickname">${user.nickname}</div>
                            <div class="user-email muted">${user.email}</div>
                        </div>
                    </div>
                    ${user.id !== myId ? `
                    <button class="${is_following ? 'secondary' : ''}" style="padding: 5px 15px; font-size: 0.8rem;" onclick="event.stopPropagation(); toggleFollowInSearch(${user.id}, ${is_following}, this)">
                        ${is_following ? 'Відписатися' : 'Підписатися'}
                    </button>
                    ` : ''}
                `;
                usersList.appendChild(userCard);
            }
        }

        // Render Drawings
        await renderDrawings(results.drawings, 'drawings-list');

    } catch (e) {
        console.error(e);
        showStatus('Помилка завантаження результатів пошуку', true);
    }
}

async function loadFeed(q = null) {
    const list = document.getElementById('drawings-list');
    if (!list) return;
    try {
        let url = '/drawings/feed';
        const params = new URLSearchParams();
        if (q) {
            params.append('q', q);
        }
        if (params.toString()) {
            url += `?${params.toString()}`;
        }
        let res = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.status === 401) return logout();
        let drawings = await res.json();
        
        await renderDrawings(drawings, 'drawings-list');
    } catch (e) { 
        console.error(e);
        showStatus('Помилка завантаження стрічки', true); 
    }
}


// Check auth status
function checkAuth() {
    const logoutBtn = document.getElementById('nav-logout');
    if (!token && !window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
        window.location.href = '/login';
    } else if (token) {
        if (logoutBtn) logoutBtn.style.display = 'inline';
        const userEmailSpan = document.getElementById('current-user-email');
        if (userEmailSpan) userEmailSpan.innerText = userEmail;
    } else {
        if (logoutBtn) logoutBtn.style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    
    // Set up search form listener
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearch);
    }
});
