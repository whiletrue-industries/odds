var odds___html = `
<div id="odds">
    <div class='trigger'>
        <span>חיפוש מידע</span>
        <span>בעזרת AI</span>
    </div>
    <div class='popup closed'><iframe src='https://ask.datadeepsearch.io/m/odata'></iframe></div> 
    <div class='close'>X</div>
</div>
`;

let odds___css = `
#odds {
    z-index: 9999;
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 100%;
    padding: 16px;
    overflow: visible;
    pointer-events: none;
    font-family: 'Assistant', sans-serif;
}
#odds .trigger {
    position: absolute;
    bottom: 0;
    left: 0;
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
    background-image: url('https://ask.datadeepsearch.io/embed/odds-trigger.svg');
    background-size: 98px 98px;
    background-repeat: no-repeat;
    background-position: center;
    border-radius: 50%;
}
#odds .popup {
    width: 100%;
    max-width: 512px;
    height: calc(100% - 116px);
    max-height: 800px;
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
    box-shadow: 0px 4px 24px rgba(0, 0, 0, 0.7);
    border: 1px solid white;
}

#odds .close {
    color: #888;
    font-size: 14px;
    position: absolute;
    bottom: 0;
    left: 0;
    pointer-events: all;
}
`;

var odds___onload = null;
odds___load = function() {
    odds___onload ? odds___onload() : null;
    var body = document.getElementsByTagName('body')[0];
    console.log(body);
    // Create element in body based on html, add css to head
    var div = document.createElement('div');
    div.innerHTML = odds___html;
    body.appendChild(div);
    var style = document.createElement('style');
    style.innerHTML = odds___css;
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
    // Add event listener to close button
    var close = document.querySelector('.close');
    close.addEventListener('click', function() {
        document.body.removeChild(div);
    });
}
    
if (document.readyState === "complete") {
    console.log('Loading odds post load');
    odds___load();
} else {
    console.log('Loading odds');
    odds___onload = window.onload;
    window.onload = odds___load;
}
