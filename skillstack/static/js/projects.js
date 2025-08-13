
//Helper functions - KR 13/08/2025
function $(sel, ctx) {return (ctx || document).querySelector(sel); } //Selects first element on the page that matches the CSS selector given.
function $all(sel, ctx) {return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); } //Selects all matching elements and returns them as an array.
function on(el, ev, fn, opts){if (el) el.addEventListener(ev, fn, opts || false); } //Adds event listener.
function formatBytes(bytes){                                                       //Takes a file size in bytes and turns it into mb, gb or tb.
    if (!Number.isFinite(bytes)) return '0 B';
    const units = ['B', 'KB', 'MB', 'TB'];
    let i = 0, v = bytes;
    while (v>= 1024 && i < units.length - 1) {v /=1024; i++; }
    return v.toFixed(v >= 10 || i === 0 ? 0 : 1) + ' ' + units[i];
} 

//Drag & drop upload - KR 13/08/2025
(function uploadEnhancements(){ //Looks for the upload form. Script stops running if it doesn't exist.
    const form = document.querySelector('form[action*="attachments/upload"]');
    if (!form) return;
    const dz = $('.upload-dropzone'. form) || form;
    const fileinput = $('input[type="file"]', form);
    if (!fileinput) return;

})

//Create live file list under the dropzone - KR 13/08/2025
let list = document.createElement('div');
list.className = 'upload-file-list small text-muted';
dz.insertAdjacentElement('afterend', list); //creates section after dropzone to show the selected file & total size.

function renderList(files){ //displays file name & its size. Also shows total size at the bottom. This is called whenever teh file changes.
    if (!files || !files.length){
        list.innerHTML = '';
        return;
    }
    let total = 0;
    let html = '<ul class="mb-1">';
    Array.from(files).forEach(f => {
        total += f.size || 0;
        html += '<li class="text-truncate">${f.name} <span class="text-secondary">(${formatBytes(f.size || 0)})</span></li>';
    });
    html += '</ul>';
    html += '<div class="text-secondary">Total: <strong>${formatBytes(total)}</strong></div>';
    list.innerHTML = html;
}

on(fileInput, 'change', e => renderList(e.target.files)); //When files are picked through the standard input, they will render on the list.