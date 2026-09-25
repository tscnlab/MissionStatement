// Exercise the shipped selector script without a browser or a server.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync('_site/compare.html', 'utf8');
const json = html.match(/<script[^>]*id="comparison-data"[^>]*>([\s\S]*?)<\/script>/)[1];
const data = JSON.parse(json);
const elements = {};
for (const id of ['comparison-data', 'version-from', 'version-to', 'show-unchanged', 'comparison-results', 'comparison-announcement', 'comparison-link']) {
  elements[id] = {value: '', checked: true, textContent: '', innerHTML: '', handlers: {},
    addEventListener(event, handler) { this.handlers[event] = handler; },
    querySelectorAll() { return []; }};
}
elements['comparison-data'].textContent = json;
const window = {
  location: {href: 'https://example.org/MissionStatement/compare.html?from=unknown&to=v1.5', search: '?from=unknown&to=v1.5'},
  history: {replaceState(_state, _title, url) { window.location.href = url; }},
  addEventListener() {},
};
vm.runInNewContext(fs.readFileSync('assets/compare.js', 'utf8'), {
  document: {getElementById: id => elements[id]}, window, URL, URLSearchParams,
});
assert.equal(elements['version-from'].value, data.defaultFrom, 'Invalid URL versions must fall back safely');
for (const from of data.versions) {
  for (const to of data.versions) {
    elements['version-from'].value = from.id;
    elements['version-to'].value = to.id;
    elements['version-to'].handlers.change();
    assert.equal(elements['comparison-results'].innerHTML, data.comparisons[`${from.id}:${to.id}`].html);
    assert.equal(new URL(elements['comparison-link'].href).searchParams.get('from'), from.id);
    assert.equal(new URL(elements['comparison-link'].href).searchParams.get('to'), to.id);
  }
}
const unchanged = [{hidden: false}, {hidden: false}];
elements['comparison-results'].querySelectorAll = () => unchanged;
elements['show-unchanged'].checked = false;
elements['show-unchanged'].handlers.change();
assert.ok(unchanged.every(section => section.hidden));
elements['show-unchanged'].checked = true;
elements['show-unchanged'].handlers.change();
assert.ok(unchanged.every(section => !section.hidden));
console.log(`Verified selectors, share links and unchanged-section controls for ${data.versions.length ** 2} version pairs.`);
