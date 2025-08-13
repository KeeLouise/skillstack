
//Helper functions - KR 13/08/2025
function $(sel, ctx) {return (ctx || document).querySelector(sel); } //Selects first element on the page that matches the CSS selector given
function $all(sel, ctx) {return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); } //Selects all matching elements and returns them as an array
function on(el, ev, fn, opts){if (el) el.addEventListener(ev, fn, opts || false); } //Adds event listener
function formatBytes(bytes){                                                       //Takes a file size in bytes and turns it into mb, gb or tb
    if (!Number.isFinite(bytes)) return '0 B';
    const units = ['B', 'KB', 'MB', 'TB'];
    let i = 0, v = bytes;
    while (v>= 1024 && i < units.length - 1) {v /=1024; i++; }
    return v.toFixed(v >= 10 || i === 0 ? 0 : 1) + ' ' + units[i];
} 