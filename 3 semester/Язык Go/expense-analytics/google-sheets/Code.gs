/**
 * Expense Analytics — Google Apps Script bridge
 *
 * Листы:
 *  - Settings: API_BASE_URL, EMAIL, PASSWORD, TOKEN
 *  - Transactions: date | amount | category | description | status
 *  - Budgets: category | limit_amount | period | status
 *  - Report: заполняется автоматически
 */

var SETTINGS_SHEET = 'Settings';
var TX_SHEET = 'Transactions';
var BUDGET_SHEET = 'Budgets';
var REPORT_SHEET = 'Report';

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Expense Analytics')
    .addItem('Login / Refresh JWT', 'loginAndStoreToken')
    .addItem('Sync new transactions', 'syncTransactions')
    .addItem('Sync budgets', 'syncBudgets')
    .addItem('Load summary report', 'loadReport')
    .addToUi();
}

function getSettings() {
  var sh = SpreadsheetApp.getActive().getSheetByName(SETTINGS_SHEET);
  if (!sh) throw new Error('Create sheet "Settings" with keys API_BASE_URL, EMAIL, PASSWORD');
  var values = sh.getDataRange().getValues();
  var map = {};
  values.forEach(function (row) {
    if (row[0]) map[String(row[0]).trim()] = String(row[1] || '').trim();
  });
  return map;
}

function setSetting(key, value) {
  var sh = SpreadsheetApp.getActive().getSheetByName(SETTINGS_SHEET);
  var values = sh.getDataRange().getValues();
  for (var i = 0; i < values.length; i++) {
    if (String(values[i][0]).trim() === key) {
      sh.getRange(i + 1, 2).setValue(value);
      return;
    }
  }
  sh.appendRow([key, value]);
}

function apiFetch(path, method, payload, token) {
  var settings = getSettings();
  var url = settings.API_BASE_URL.replace(/\/$/, '') + path;
  var options = {
    method: method || 'get',
    contentType: 'application/json',
    muteHttpExceptions: true,
    headers: {
      // free ngrok interstitial bypass for UrlFetchApp / API clients
      'ngrok-skip-browser-warning': 'true'
    }
  };
  if (token) options.headers.Authorization = 'Bearer ' + token;
  if (payload) options.payload = JSON.stringify(payload);
  var resp = UrlFetchApp.fetch(url, options);
  var code = resp.getResponseCode();
  var body = resp.getContentText();
  var json = {};
  try { json = JSON.parse(body); } catch (e) { json = { raw: body }; }
  return { code: code, json: json, body: body };
}

function loginAndStoreToken() {
  var settings = getSettings();
  var result = apiFetch('/api/auth/login', 'post', {
    email: settings.EMAIL,
    password: settings.PASSWORD
  });
  if (result.code >= 300) {
    // fallback: register then login
    apiFetch('/api/auth/register', 'post', {
      email: settings.EMAIL,
      password: settings.PASSWORD,
      name: settings.NAME || 'Sheets User'
    });
    result = apiFetch('/api/auth/login', 'post', {
      email: settings.EMAIL,
      password: settings.PASSWORD
    });
  }
  if (result.code >= 300) {
    throw new Error('Auth failed: ' + result.body);
  }
  setSetting('TOKEN', result.json.access_token);
  SpreadsheetApp.getActive().toast('JWT сохранён', 'Expense Analytics', 3);
  return result.json.access_token;
}

function ensureToken() {
  var settings = getSettings();
  if (settings.TOKEN) return settings.TOKEN;
  return loginAndStoreToken();
}

function syncTransactions() {
  var token = ensureToken();
  var sh = SpreadsheetApp.getActive().getSheetByName(TX_SHEET);
  var data = sh.getDataRange().getValues();
  for (var i = 1; i < data.length; i++) {
    var row = data[i];
    var status = String(row[4] || '');
    if (status === 'OK' || !row[0]) continue;
    var date = Utilities.formatDate(new Date(row[0]), Session.getScriptTimeZone(), 'yyyy-MM-dd');
    var result = apiFetch('/api/transactions', 'post', {
      date: date,
      amount: Number(row[1]),
      category: String(row[2]),
      description: String(row[3] || '')
    }, token);
    sh.getRange(i + 1, 5).setValue(result.code < 300 ? 'OK' : ('ERR ' + result.code + ': ' + result.body));
  }
  SpreadsheetApp.getActive().toast('Транзакции отправлены', 'Expense Analytics', 3);
}

function syncBudgets() {
  var token = ensureToken();
  var sh = SpreadsheetApp.getActive().getSheetByName(BUDGET_SHEET);
  var data = sh.getDataRange().getValues();
  for (var i = 1; i < data.length; i++) {
    var row = data[i];
    var status = String(row[3] || '');
    if (status === 'OK' || !row[0]) continue;
    var result = apiFetch('/api/budgets', 'post', {
      category: String(row[0]),
      limit_amount: Number(row[1]),
      period: String(row[2] || 'monthly')
    }, token);
    sh.getRange(i + 1, 4).setValue(result.code < 300 ? 'OK' : ('ERR ' + result.code + ': ' + result.body));
  }
  SpreadsheetApp.getActive().toast('Бюджеты сохранены', 'Expense Analytics', 3);
}

function loadReport() {
  var token = ensureToken();
  var settings = getSettings();
  var from = settings.REPORT_FROM || '2024-01-01';
  var to = settings.REPORT_TO || Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd');
  var result = apiFetch('/api/reports/summary?from=' + encodeURIComponent(from) + '&to=' + encodeURIComponent(to), 'get', null, token);
  if (result.code >= 300) throw new Error(result.body);

  var ss = SpreadsheetApp.getActive();
  var sh = ss.getSheetByName(REPORT_SHEET) || ss.insertSheet(REPORT_SHEET);
  sh.clear();
  sh.getRange(1, 1, 1, 5).setValues([['from', 'to', 'total_spent', 'cache_hit', 'generated_at']]);
  sh.getRange(2, 1, 1, 5).setValues([[
    result.json.from,
    result.json.to,
    result.json.total_spent,
    result.json.cache_hit,
    new Date().toISOString()
  ]]);
  sh.getRange(4, 1, 1, 5).setValues([['category', 'spent', 'budget_limit', 'budget_usage_percent', 'over_budget']]);
  var cats = result.json.categories || [];
  if (cats.length) {
    var rows = cats.map(function (c) {
      return [c.category, c.spent, c.budget_limit, c.budget_usage_percent, c.over_budget];
    });
    sh.getRange(5, 1, rows.length, 5).setValues(rows);
  }
  SpreadsheetApp.getActive().toast('Отчёт загружен (cache_hit=' + result.json.cache_hit + ')', 'Expense Analytics', 4);
}
