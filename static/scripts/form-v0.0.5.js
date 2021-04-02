$(() => {
    const SMOOTHING_FACTOR = 5;
    const form = $('#submission-form'), code = $('#code'),
            response = $('#response'), progressBar = $('#progress'),
            submitButton = form.find('button[type="submit"]');
    const maxProgress = (MAX_EXECUTION / 1000) * EXECUTIONS * SMOOTHING_FACTOR;

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

        response.html('');
        timer = setInterval(() => {
            const percent = progress / maxProgress * 100;
            console.log(percent)
            submitButton.addClass('is-hidden');
            progressBar.removeClass('is-hidden')
            progressBar.val(percent); 
            progressBar.html(`${progress.toFixed(2)}%`);
            progress += 1;
        }, 1000 / SMOOTHING_FACTOR);
        fetch(`run?${form.serialize()}`, {
            method: 'POST',
            body: code.val()
        }).then(res => res.text())
        .then(data => {
            response.html(data);
            resetTimer();
        }).catch(e => {
            console.error(e);
            alert('Unknown timeout error!');
            resetTimer();
        })
        event.preventDefault();
    });


    const recomputeTimer = $('#timer');
    var countDownDate = nextTime();

    function nextTime() {
        const cron = cronSchedule.parseCronExpression(COMPUTE_SCHEDULE)
        return cron.getNextDate(new Date(Date.now()));
    }

    function pad(n, width, z) {
        z = z || '0';
        n = n + '';
        return n.length >= width ? n : new Array(width - n.length + 1).join(z) + n;
    }

    setInterval(() => {
        const now = new Date().getTime();
        const timeleft = countDownDate - now;

        if (timeleft < 0) {
            countDownDate = nextTime();
            location.reload()
        }
            
        const hours = Math.floor((timeleft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((timeleft % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((timeleft % (1000 * 60)) / 1000);

        recomputeTimer.text(`${pad(hours, 2)}:${pad(minutes, 2)}:${pad(seconds, 2)}`)
    }, 1000);
});
