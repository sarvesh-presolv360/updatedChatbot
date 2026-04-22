(function () {
  'use strict';

  // Read API base URL from the script tag's data-api-url attribute.
  // Falls back to same-origin (works when page and API are on the same domain).
  var _script = document.currentScript;
  var API_BASE = (_script && _script.getAttribute('data-api-url')) || '';

  var CHATKIT_CDN = 'https://cdn.platform.openai.com/deployments/chatkit/chatkit.js';
  var SESSION_URL = API_BASE + '/api/create-session';

  var styles = `
    #wedgie-btn {
      position: fixed;
      bottom: 28px;
      right: 28px;
      z-index: 9998;
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: #1a1a2e;
      border: none;
      cursor: pointer;
      box-shadow: 0 4px 16px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    #wedgie-btn:hover {
      transform: scale(1.08);
      box-shadow: 0 6px 20px rgba(0,0,0,0.4);
    }
    #wedgie-btn svg { pointer-events: none; }

    #wedgie-panel {
      position: fixed;
      bottom: 96px;
      right: 28px;
      z-index: 9999;
      width: 380px;
      height: 600px;
      max-height: calc(100vh - 120px);
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 8px 32px rgba(0,0,0,0.25);
      display: none;
      flex-direction: column;
      background: #fff;
    }
    #wedgie-panel.open { display: flex; }

    #wedgie-header {
      background: #1a1a2e;
      color: #fff;
      padding: 14px 16px;
      font-family: sans-serif;
      font-size: 15px;
      font-weight: 600;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    #wedgie-close {
      background: none;
      border: none;
      color: #fff;
      cursor: pointer;
      font-size: 20px;
      line-height: 1;
      padding: 0;
      opacity: 0.8;
    }
    #wedgie-close:hover { opacity: 1; }

    #wedgie-body {
      flex: 1;
      overflow: hidden;
      position: relative;
    }
    #wedgie-body openai-chatkit {
      width: 100%;
      height: 100%;
      display: block;
    }
    #wedgie-loader {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: sans-serif;
      font-size: 14px;
      color: #666;
      background: #fff;
    }

    @media (max-width: 480px) {
      #wedgie-panel {
        right: 0;
        bottom: 0;
        width: 100%;
        height: 100%;
        max-height: 100%;
        border-radius: 0;
      }
      #wedgie-btn { bottom: 16px; right: 16px; }
    }
  `;

  function injectStyles() {
    var el = document.createElement('style');
    el.textContent = styles;
    document.head.appendChild(el);
  }

  function injectHTML() {
    var btn = document.createElement('button');
    btn.id = 'wedgie-btn';
    btn.setAttribute('aria-label', 'Open chat');
    btn.innerHTML = `
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>`;
    document.body.appendChild(btn);

    var panel = document.createElement('div');
    panel.id = 'wedgie-panel';
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-modal', 'true');
    panel.setAttribute('aria-label', 'Presolv360 Assistant');
    panel.innerHTML = `
      <div id="wedgie-header">
        <span>Presolv360 Assistant</span>
        <button id="wedgie-close" aria-label="Close chat">&times;</button>
      </div>
      <div id="wedgie-body">
        <div id="wedgie-loader">Loading…</div>
      </div>`;
    document.body.appendChild(panel);

    return { btn: btn, panel: panel };
  }

  var initialized = false;

  function loadChatKitScript(cb) {
    if (document.querySelector('script[src="' + CHATKIT_CDN + '"]')) {
      cb();
      return;
    }
    var s = document.createElement('script');
    s.src = CHATKIT_CDN;
    s.async = true;
    s.onload = cb;
    document.head.appendChild(s);
  }

  function initChatKit(body) {
    var loader = document.getElementById('wedgie-loader');

    loadChatKitScript(function () {
      var ck = document.createElement('openai-chatkit');

      // The component calls getClientSecret whenever it needs a fresh token.
      // We fetch it from our FastAPI backend using the absolute URL.
      ck.setOptions({
        api: {
          getClientSecret: function () {
            return fetch(SESSION_URL, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({}),
            })
              .then(function (r) {
                if (!r.ok) throw new Error('Session error ' + r.status);
                return r.json();
              })
              .then(function (data) {
                return data.client_secret;
              });
          },
        },
        theme: 'light',
        accentColor: '#1a1a2e',
      });

      if (loader) loader.remove();
      body.appendChild(ck);
      initialized = true;
    });
  }

  function init() {
    injectStyles();
    var els = injectHTML();
    var btn = els.btn;
    var panel = els.panel;
    var body = document.getElementById('wedgie-body');
    var isOpen = false;

    function openPanel() {
      panel.classList.add('open');
      btn.setAttribute('aria-expanded', 'true');
      isOpen = true;
      if (!initialized) initChatKit(body);
    }

    function closePanel() {
      panel.classList.remove('open');
      btn.setAttribute('aria-expanded', 'false');
      isOpen = false;
    }

    btn.addEventListener('click', function () {
      isOpen ? closePanel() : openPanel();
    });

    document.getElementById('wedgie-close').addEventListener('click', closePanel);

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && isOpen) closePanel();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
