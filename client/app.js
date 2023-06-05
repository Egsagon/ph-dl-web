/* Utilities */

xhr = (url, callback, body = null, method = 'GET') => {
    /* Start an XHR request */

    req = new XMLHttpRequest()

    req.onreadystatechange = () => {
        if (req.readyState == 4) { callback(req) }
    }

    req.open(method, url)
    req.send(body)
}

video_template = `
<div class='tkn-{{tokn}}'>
    <img></img>
    <p>{{title}}</p>
    <a download disabled><i class='fa fa-cloud-download'></i></a>
</div>
<div class='bar'>
    <div></div>
</div>
`

/* Handle connecting with the backend */

update = (token, q, next) => {
    /* Update backend download status for one session/token */

    xhr('/status?token=' + token, res => {

        response = JSON.parse(res.response)

        console.log('Uptated', token, '=>', response.progress)

        // Update title and thumbnail
        video = get('.tkn-' + token)

        if (response.fail) {
            // Display error
            get('p', 0, video).innerHTML = 'Failed'
            video.removeChild(get('img', 0, video))
            bar = get('.bar > div', 0, video.parentNode)
            bar.innerHTML = 'Error'
            bar.style.width = '100%'
            notificate('Error', response.error, 4000, 'exclamation-circle')
            
            // Pass on to next URL
            return download(next, q)
        }

        if (response.progress == null) {
            // Avoid errors when video not treated yet
            get('p', 0, video).innerHTML = 'In queue...'    
            return setTimeout(update, 3000, token, q, next)
        }
        
        get('img', 0, video).src = response.image
        get('p', 0, video).innerHTML = response.title

        // Update progress
        percent = Math.round(((response.progress + 1) / response.total) * 100)
        bar = get('.bar > div', 0, video.parentNode)
        
        bar.innerHTML = percent + '%'
        bar.style.width = percent + '%' // TODO adjust min and max
        document.title = 'PH DL - ' + percent + '%'

        if (percent == 100) {
            // Show download button
            link = get('a', 0, video)
            link.disabled = null
            link.style.cursor = 'pointer'
            link.style.backgroundColor = 'var(--ac)'
            link.href = response.path

            // Stop the loop / start other downloads if needed
            return download(next, q)
        }

        // Repeat
        setTimeout(update, 3000, token, q, next)
    })
}

get('#query').addEventListener('submit', ev => {
    ev.preventDefault()

    // Get download URLs
    us = []
    get('#queries input', 1).forEach(ub => {us.push(ub.value)})

    // Remove precedent videos
    get('.thumb', 1).forEach(node => node.remove())

    // Start the download
    download(us, get('#quality').value)
})

download = (requests, qual) => {

    // Avoid infinite loops
    if (!requests.length) { return }

    // Remove duplicates
    requests = [...new Set(requests)]

    console.log('Using', requests)

    // Send the request
    current = requests.shift()

    // Wrong URL protection
    if (!/https:\/\/..\.pornhub\.com\/view.*/gm.test(current)) {
        return notificate('Error', 'The URL does not seem right.')
    }

    xhr(`/download?url=${current}&quality=${qual}`, res => {

        tkn = res.response
        console.log('Posted', current, '=>', tkn)

        // Show errors
        if (tkn.includes('error:')) {
            return notificate('Error', tkn)
        }

        // Show videos thumbnails
        box = document.createElement('div')
        box.classList.add('thumb')
        box.innerHTML = format(video_template,
                                {'tokn': tkn, 'title': '...'})

        get('#videos').appendChild(box)

        // Show content section
        content_toggle(1)

        // Start udpate loop
        setTimeout(update, 1000, tkn, qual, requests)

    }, null, 'POST')
}

download_all = () => {
    /* Download all videos from server */

    // Check that all videos are ready
    get('.bar div', 1).forEach(bar => {
        ok = bar.style.width.includes('100%')

        if (!ok) {
            return notificate('Wait!', 'Some downloads are not finished yet!',
                              4000, 'exclamation-circle')
        }
    })

    get('.thumb a', 1).forEach(li => li.click())
}

// EOF