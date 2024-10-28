function parseCrsfToken() {
    let token = '';
    if (document.cookie && document.cookie !== '') {
        document.cookie.split(';').forEach(function (c) {
            const m = c.trim().match(/(\w+)=(.*)/);  // matches "name=value" pattern
            if (m !== undefined && m[1] === 'csrftoken') {  // if name is "csrftoken"
                token = decodeURIComponent(m[2]);  // decode the value part
            }
        });
    }
    return token;
}

var crsfToken = parseCrsfToken();

function upvote(item) {
    let id = item.id.substring(3);  // crop "up_" from ids like "up_100"
    let url = item.dataset.upvoteUrl;

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': crsfToken
        },
    }).then(res => res.json())
    .then(res => {
        let scoreItem;
        if (res.success) {
            // fetch points element and update it
            scoreItem = document.getElementById('score_' + id);
            scoreItem.innerText = `${res.nlikes} point${res.nlikes !== 1 ? 's' : ''}`;
        } else {
            window.location = item.dataset.redirectUrl;
        }
    }).catch(error => console.log(error));
}

function upvotePost(item) {
    upvote(item, 'post')
}

function upvoteComment(item) {
    upvote(item, 'comment')
}