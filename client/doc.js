/* Utilities */

get = (selector, multiple = false, parent = document) => {
    /* Shorthand for querySelector */

    if (multiple) { return parent.querySelectorAll(selector) }
    return parent.querySelector(selector)
}

format = (str, dict) => {
    /* Equivalent of str.format in python with double {} */

    for (let [key, value] of Object.entries(dict)) {
        str = str.replace(`{{${key}}}`, value)
    }
    return str

}

notification_template = get('.notification.template').innerHTML

notificate = (title, text, time = 4000, icon = 'info-circle') => {
    /* Send a notification */

    // Create the note
    note = document.createElement('div')
    note.classList.add('notification')
    note.innerHTML = format(notification_template,
        {'title': title, 'text': text, 'icon': icon})

    // Add to document
    document.body.appendChild(note)

    // Animate
    note.style.animation = 'notificate 2s forwards'

    // Hide after timeout
    setTimeout(() => {
        note.style.animation = 'hide-notification 2s forwards'
    }, time)

    // Obliterate the popup
    setTimeout(() => {document.body.removeChild(note)}, time + 2000)
}

// Display first time message
if (0 && !document.cookie.includes('used=1;')) {

    notificate('Hello, world!', 'Press <kb>del</kb> to delete URL boxes!')

    // Set used cookie
    d = new Date()
    d.setTime(d.getTime() + 1209600000) // reset each week
    document.cookie = `used=1;expires=${d.toUTCString()};SameSite=Strict;path=/`
}

/* Document reactions */

query_drop = get('#dropdown')
content = get('#content')

query_drop_toggle = (node) => {
    /* Toggle the filters dropdown menu */

    b = node.checked ? 'show-dropdown 1' : 'hide-dropdown 2'
    query_drop.style.animation = b + 's forwards'

}

get('#add_query_field').onclick = (ev) => {
    /* Add a new url field */

    ev.preventDefault()
    get('#queries').appendChild(document.createElement('input')) // TODO bind enter to dl func

    // Reload bindings
    bind_urlboxes()

}

bind_urlboxes = () => {

    get('#queries input', true).forEach(urlbox => {
        /* Bind deletion of urlboxes */

        urlbox.addEventListener('keyup', ev => {

            if (get('#queries input', true).length <= 1) { return }

            if (ev.keyCode == 46) { urlbox.remove() }
        })
    })
}

content_toggle = (bool) => {
    /* Toggle opening/closing the content section */

    b = bool ? 'show-content 1' : 'hide-content 2'
    content.style.animation = b + 's forwards'
}


bind_urlboxes()

// EOF