(function () {
  'use strict';

  var MCP = { host: '127.0.0.1', port: 9222, http: '', ws: '', version: '2.8.0' };

  function $(sel) { return document.querySelector(sel); }
  function $all(sel) { return document.querySelectorAll(sel); }

  function applyApi(api) {
    if (!api) return;
    MCP.version = api.version || MCP.version;
    if (api.mcp_http_post) {
      try {
        var u = new URL(api.mcp_http_post);
        MCP.host = u.hostname;
        MCP.port = u.port || MCP.port;
        MCP.http = u.origin;
      } catch (e) {}
    }
    if (api.mcp_ws) MCP.ws = api.mcp_ws;
    document.querySelectorAll('[data-dynamic]').forEach(function (el) {
      var key = el.getAttribute('data-dynamic');
      var val = '';
      if (key === 'http') val = MCP.http;
      else if (key === 'ws') val = MCP.ws;
      else if (key === 'version') val = MCP.version;
      else if (key === 'host') val = MCP.host;
      else if (key === 'port') val = MCP.port;
      else if (key === 'post') val = MCP.http + '/mcp';
      if (val) el.textContent = val;
    });
    var cfg = {
      mcpServers: {
        'ai-browser': {
          command: 'node',
          args: ['CEFbro/AI浏览器/mcp_bridge.js'],
          env: {
            AI_BROWSER_MCP_HOST: MCP.host,
            AI_BROWSER_MCP_PORT: String(MCP.port),
            AI_BROWSER_MCP_HTTP_POST: MCP.http + '/mcp',
            AI_BROWSER_MCP_CURSOR_MODE: '0'
          }
        }
      }
    };
    var cfgEl = $('#cursorConfig');
    if (cfgEl) cfgEl.textContent = JSON.stringify(cfg, null, 2);
  }

  function initNav() {
    var links = $all('.nav a');
    var sections = [];
    links.forEach(function (a) {
      var id = (a.getAttribute('href') || '').replace('#', '');
      if (id) {
        var sec = document.getElementById(id);
        if (sec) sections.push({ link: a, sec: sec });
      }
    });
    function onScroll() {
      var y = window.scrollY + 100;
      var cur = sections[0];
      sections.forEach(function (s) {
        if (s.sec.offsetTop <= y) cur = s;
      });
      links.forEach(function (a) { a.classList.remove('active'); });
      if (cur) cur.link.classList.add('active');
    }
    window.addEventListener('scroll', onScroll);
    onScroll();
  }

  window.copyBlock = function (id, btn) {
    var el = document.getElementById(id);
    if (!el) return;
    var text = el.textContent || el.innerText;
    navigator.clipboard.writeText(text).then(function () {
      if (btn) {
        var old = btn.textContent;
        btn.textContent = '已复制';
        btn.classList.add('copied');
        setTimeout(function () { btn.textContent = old; btn.classList.remove('copied'); }, 2000);
      }
    });
  };

  function loadToolsSummary() {
    var base = MCP.http || ('http://' + MCP.host + ':' + MCP.port);
    fetch(base + '/tools/list').then(function (r) { return r.json(); }).then(function (d) {
      var el = $('#toolCountLive');
      if (el && d.tools) el.textContent = d.tools.length;
      var grid = $('#toolCategoryGrid');
      if (!grid || !d.tools) return;
      var cats = [
        { name: '导航与页面', re: /navigate|get_url|get_title|reload|back|forward|stop|browser_list|status/ },
        { name: 'JS / DOM / 填表', re: /execute_js|evaluate|dom_|fill_/ },
        { name: '输入 / 触摸', re: /mouse_|key_|touch_|edit_/ },
        { name: '网络 / CDP / 调试', re: /cdp|network|collect|wait|inject|event|intercept/ },
        { name: 'VIP 高级', re: /vip_/ },
        { name: '工作流 / 编排', re: /workflow_/ },
        { name: '系统 / 其他', re: /mcp_|ping|batch|proxy|cookie|screenshot|aliases/ }
      ];
      var html = '';
      cats.forEach(function (cat) {
        var n = 0;
        d.tools.forEach(function (t) { if (cat.re.test(t.name || '')) n++; });
        html += '<div class="card" style="padding:12px 14px"><strong>' + cat.name + '</strong><br><span style="color:var(--muted);font-size:.85em">' + n + ' 个工具</span></div>';
      });
      grid.innerHTML = html;
    }).catch(function () {});
  }

  var base = window.location.origin;
  fetch(base + '/api').then(function (r) { return r.json(); }).then(function (api) {
    applyApi(api);
    loadToolsSummary();
  }).catch(function () {
    MCP.http = base;
    MCP.ws = base.replace('http', 'ws');
    applyApi(null);
    loadToolsSummary();
  });

  document.addEventListener('DOMContentLoaded', initNav);
})();
