class window.Controls.timeprogressbar extends window.Controls.hc
    setupDom: (dom) ->
        super(dom)
        @time = @properties.time
        @maxtime = @properties.maxtime

        label = new Controls.label(@ui)
        bar = new Controls.progressbar(@ui, width: @properties.width)

        label.setupDom()
        bar.setupDom()

        @append(label)
        @append(bar)

        @setTime(@time)
        if @properties.started
            @start()
        else
            @stop()

        $(@dom).find('.progressbar').css 'margin-left': '5px', 'margin-right': '5px'

        return this

    formatTime: (time) ->
        seconds = time % 60
        minutes = (time / 60) >> 0
        hours = (time / 3600) >> 0
        days = (time / 86400) >> 0

        format = (value) -> if (value < 10) then '0' + value else '' + value

        value = "#{format(minutes)}:#{format(seconds)}"
        value = "#{hours}:#{value}" if hours
        value = "#{days} day#{'s' if days != 1}, #{values}" if days
        return value

    setTime: (time) ->
        @time = time
        p = time / @maxtime
        pw = @_int_to_px Math.round(@properties.width * p)
        $(@dom).find('.fill').css width: pw
        $(@dom).find('.label').text "#{@formatTime(time)} / #{@formatTime(@maxtime)}"

    start: ->
        return if @interval
        @interval = setInterval (=> @tick()), 1000
        @tick()

    tick: ->
        @setTime @time + 1
        # console.log @time, @dom.parentNode
        @stop() unless (@dom.parentNode isnt null) and (not @maxtime or @time < @maxtime)

    stop: ->
        return unless @interval
        clearInterval @interval
        @interval = null

    destruct: ->
        super()
        @stop()

