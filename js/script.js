$(document).ready(function () {
    const phoneField = $('#phone');
    phoneField.on('click', function () {
        const s = '43514932405441325355325255325550324956';
        let res = '';
        for (let i = 0; i < s.length; i += 2) {
            res += String.fromCharCode(Number.parseInt(s.slice(i, i + 2)));
        }
        phoneField.text(res);
        phoneField.removeClass('hidden');
    });
});