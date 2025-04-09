let html = `
<div id="odds" style="position: fixed; bottom: 16px; left: 16px; z-index: 9999;">
    <div class='trigger'>
        <span>חיפוש מידע</span>
        <span>בעזרת AI</span>
    </div>
    <div class='popup closed'><iframe src='http://localhost:4200/m/odata'></iframe></div> 
</div>
`;

let css = `
#odds {
    z-index: 9999;
    position: fixed;
    bottom: 16px;
    left: 16px;
    overflow: visible;
    pointer-events: none;
    font-family: 'Assistant', sans-serif;
}
#odds .trigger {
    width: 100px;
    height: 100px;
    pointer-events: all;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    font-size: 16px;
    line-height: 100%;
    background-image: url('/odds-trigger.svg');
    background-size: 98px 98px;
    background-repeat: no-repeat;
    background-position: center;
    border-radius: 50%;
}
#odds .popup {
    width: 512px;
    max-width: calc(100vw - 32px);
    height: 800px;
    max-height: calc(100vh - 132px);
    position: absolute;
    bottom: 100px;
    left: 0px;
    border-radius: 8px;
    overflow: hidden;
    display: none;

    iframe {
        width: 100%;
        height: 100%;
        border: none;
    }
}
#odds .popup.open {
    display: flex;
    pointer-events: all;
    background-color: white;
    box-shadow: 0px 4px 24px rgba(0, 0, 0, 0.1);
}

`;

let onload = window.onload;

window.onload = function() {
    onload ? onload() : null;
    var body = document.getElementsByTagName('body')[0];
    console.log(body);
    // Create element in body based on html, add css to head
    var div = document.createElement('div');
    div.innerHTML = html;
    body.appendChild(div);
    var style = document.createElement('style');
    style.innerHTML = css;
    document.head.appendChild(style);
    // Load font
    var link = document.createElement('link');
    link.href = "https://fonts.googleapis.com/css2?family=Assistant:wght@700&display=swap";
    link.rel = "stylesheet";
    document.head.appendChild(link);
    // Add event listener to trigger
    var trigger = document.querySelector('.trigger');
    trigger.addEventListener('click', function() {
        var popup = document.querySelector('.popup');
        if (popup.classList.contains('closed')) {
            popup.classList.remove('closed');
            popup.classList.add('open');
        } else {
            popup.classList.remove('open');
            popup.classList.add('closed');
        }
    });
}
    