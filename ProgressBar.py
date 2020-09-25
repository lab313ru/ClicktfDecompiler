import sys
from time import sleep


class ProgressBar:

    def __init__(self, length=40, max_progress=100, progress_indicator='{}%', finish_caption='DONE', bg_char=' ',
                 fill_char='#', edges='[]'):
        self.length = length
        self.max_progress = max_progress
        self.progress_indicator = progress_indicator
        self.finish_caption = finish_caption
        self.bg_char = bg_char
        self.fill_char = fill_char
        self.edges = edges

        self.progress = 0
        self.center = self.length // 2

    def draw(self):
        self.bar = [self.bg_char for _ in range(self.length)]
        self.bar[0] = self.edges[0]
        self.bar[-1] = self.edges[1]
        actual_length = self.length - 2
        chars_to_fill = int((self.progress / self.max_progress) * actual_length)

        for i in range(chars_to_fill):
            self.bar[1 + i] = self.fill_char

        if self.done:
            progress_indicator = self.finish_caption
        else:
            progress_indicator = self.progress_indicator.format(round((self.progress / self.max_progress) * 100, 2))

        p_len = len(progress_indicator)
        for j, i in enumerate(range(-p_len // 2, p_len // 2)):
            self.bar[self.center + i] = progress_indicator[j]

        # sys.stdout.write('\u001B[1A\u001B[2K')
        sys.stdout.write('\r')
        sys.stdout.write(''.join(self.bar))
        if self.done:
            sys.stdout.write('\n')
        sys.stdout.flush()

    @property
    def done(self):
        return self.progress >= self.max_progress

    def increment(self, val, redraw=True):
        if not self.done:
            self.progress += val
            if redraw:
                self.draw()


if __name__ == '__main__':
    a = ProgressBar(bg_char=' ', fill_char='#', edges='[]', finish_caption='DONE', progress_indicator='{}% DONE',
                    max_progress=156)
    a.draw()
    for _ in range(156):
        a.increment(1)
        sleep(0.05)
