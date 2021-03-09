$(() => {
    const smoothFactor = 5;
    const form = $("#submission-form"), code = $("#code"),
            response = $("#response"), progressBar = $("#progress"),
            submitButton = form.find("button[type='submit']"), maxProgress = 60 * 5 * smoothFactor;
    var progress = 0, timer = null;

    function resetTimer() {
        submitButton.removeClass('is-hidden');
        progressBar.addClass('is-hidden')
        clearInterval(timer);
        timer = null;
        progress = 0;
    }

    form.submit(( event ) => {
        event.preventDefault();
        if (timer != null) return;
        timer = setInterval(() => {
            const percent = progress / maxProgress * 100;
            console.log(percent)
            submitButton.addClass('is-hidden');
            progressBar.removeClass('is-hidden')
            progressBar.val(percent); 
            progressBar.html(`${progress.toFixed(2)}%`);
            progress += 1;
        }, 1000 / smoothFactor); 
        fetch(`run?${form.serialize()}`, {
            method: 'POST',
            body: code.val()
        }).then(res => res.text())
        .then(data => {
            response.html(data);
            resetTimer();
        }).catch(_ => {
            alert('Unknown timeout error!');
            resetTimer();
        })
        event.preventDefault();
    });
});
