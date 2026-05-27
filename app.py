/* ═══════════════════════════
   BACKEND LOCAL SIMULADO (Substitui a API original)
═══════════════════════════ */
function initLocalDB() {
  // Inicializa o banco de dados local se não existir
  if(!localStorage.getItem('sesi_emp')) localStorage.setItem('sesi_emp', JSON.stringify([]));
  if(!localStorage.getItem('sesi_pin')) localStorage.setItem('sesi_pin', '1234'); // PIN padrão: 1234
}
initLocalDB();

function api(url, opts) {
  opts = opts || {};
  var method = opts.method || 'GET';
  var body = opts.body ? JSON.parse(opts.body) : null;

  return new Promise(function(resolve) {
    setOnline(true);
    var emp = JSON.parse(localStorage.getItem('sesi_emp'));

    if (url === '/api/emprestimos' && method === 'GET') {
      resolve(emp);
    }
    else if (url === '/api/dispositivos-ativos' && method === 'GET') {
      var disp = { preto:[], vermelho:[], cinza:[] };
      emp.forEach(function(e) {
        if (!e.data_devolucao && e.id !== 'JBL') {
          e.numeros_dispositivos.forEach(function(n) { disp[e.carrinho].push(n); });
        }
      });
      resolve(disp);
    }
    else if (url === '/api/registrar' && method === 'POST') {
      body.data_emprestimo = new Date().toISOString();
      // Cria um ID de sessão único para permitir múltiplas retiradas com o mesmo ID
      body.session_uid = Date.now().toString(); 
      emp.push(body);
      localStorage.setItem('sesi_emp', JSON.stringify(emp));
      resolve({ok: true});
    }
    else if (url.startsWith('/api/devolver/') && method === 'PUT') {
      var idDev = decodeURIComponent(url.split('/').pop());
      emp.forEach(function(e) {
        if (e.id === idDev && !e.data_devolucao) e.data_devolucao = new Date().toISOString();
      });
      localStorage.setItem('sesi_emp', JSON.stringify(emp));
      resolve({ok: true});
    }
    else if (url.startsWith('/api/excluir/') && method === 'DELETE') {
      var idEx = decodeURIComponent(url.split('/').pop());
      emp = emp.filter(function(e) { return e.id !== idEx; }); // Remove permanentemente
      localStorage.setItem('sesi_emp', JSON.stringify(emp));
      resolve({ok: true});
    }
    else if (url === '/api/pin/verificar' && method === 'POST') {
      var pin = localStorage.getItem('sesi_pin');
      resolve({ok: (body.pin === pin)});
    }
    else if (url === '/api/pin/alterar' && method === 'POST') {
      var pin = localStorage.getItem('sesi_pin');
      if (body.pin_atual === pin) {
        localStorage.setItem('sesi_pin', body.pin_novo);
        resolve({ok: true});
      } else {
        resolve({ok: false});
      }
    }
    else {
      resolve(null);
    }
  });
}
