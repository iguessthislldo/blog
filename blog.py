#!/usr/bin/env python3

'''\
Sphinx Wrapper
'''

import sys
import os
import venv
import webbrowser
from subprocess import check_call
from shutil import rmtree
from argparse import ArgumentParser
from pathlib import Path
import http.server
import socketserver
from datetime import datetime, timezone

import docutils.nodes
import docutils.parsers.rst
import docutils.utils
import docutils.frontend


root = Path(__file__).parent
abs_root = root.resolve()
reqs_path = abs_root / 'requirements.txt'
default_venv_path = root / '.venv'
default_build_path = root / '_build'


# For icons
def hex_to_rgb(s):
    s = s[1:]
    return tuple([int(i, 16) for i in (s[0:2], s[2:4], s[4:6])] + [0xff])


name = 'iguessthislldo'
black = (0, 0, 0)
transparent = 0
theme_fg_hex = '#00ff00'
theme_bg_hex = '#282828'
theme_fg = hex_to_rgb(theme_fg_hex)
theme_bg = hex_to_rgb(theme_bg_hex)
templates_path = abs_root / '_templates'
direct_copy_path = abs_root / 'root'

# For blog generation
# TODO: Support building from somewhere other than this dir?
posts_path = Path('posts')
index_path = Path('index.rst')
tags_path = Path('tags')
now = datetime.now(timezone.utc)


def log(*args, **kwargs):
    error = kwargs.pop('error', False)
    f = sys.stderr if error else sys.stdout
    prefix = 'build.py: '
    if error:
        prefix += 'ERROR: '
    print(prefix, end='', file=f)
    print(*args, **kwargs, file=f, flush=True)


def slugify(*args, **kw):
    from slugify import slugify as _slugify
    return _slugify(*args, replacements=[["'", ''], ['"', '']], **kw)


def text_to_image(
        text: str,
        font_filepath: str,
        font_size: int,
        fg_color: (int, int, int),
        bg_color=transparent,
        margin=(0, 0),
        align='center',
        stroke_fill=(0, 0, 0),
        stroke_width=0):
    from PIL import Image, ImageFont, ImageDraw, ImageColor

    font = ImageFont.truetype(font_filepath, size=font_size)
    tmp_img = Image.new('RGBA', (10000, 10000))
    tmp_draw = ImageDraw.Draw(tmp_img)
    box = tmp_draw.multiline_textbbox(
        (0, 0), text, font=font, align=align, stroke_width=stroke_width)
    left = int(box[0])
    right = int(box[2])
    top = int(box[1])
    bottom = int(box[3])
    mx = margin[0]
    my = margin[1]
    img = Image.new('RGBA', (right - left + mx * 2, bottom - top + my * 2), bg_color)
    draw = ImageDraw.Draw(img)
    draw.multiline_text(
        (-left + mx, -top + my),
        text, font=font, fill=fg_color, align=align,
        stroke_fill=stroke_fill,
        stroke_width=stroke_width,
    )
    return img


def make(text, font_size, margin, fg_color=theme_fg, bg_color=theme_bg, **kw):
    return text_to_image(text, str(abs_root / 'monofur.ttf'), font_size, fg_color, bg_color, margin, **kw)


def save(img, name, resize=None, **kw):
    if resize is not None:
        img = img.resize((resize, resize))
    img.save(str(direct_copy_path / name), **kw)


def generate_icons():
    log('Generating icons...')

    # Logo
    def make_logo(kind, fg_color):
        save(make('%' + name, 46, (10, 10), fg_color=fg_color, bg_color=transparent), f'logo-{kind}.png')

    make_logo('light', fg_color=black)
    make_logo('dark', fg_color=theme_fg)

    # Icons
    icon = make('%', 400, (50, 20))
    save(icon, 'favicon.ico', resize=48, bitmap_format='bmp')
    save(icon, 'favicon-32x32.png', resize=32)
    save(icon, 'favicon-16x16.png', resize=16)
    save(icon, 'android-chrome-512x512.png', resize=512)
    save(icon, 'android-chrome-192x192.png', resize=192)
    save(icon, 'mstile-150x150.png', resize=150)
    save(icon, 'apple-touch-icon.png', resize=180)

    # Text Files
    (direct_copy_path / 'browserconfig.xml').write_text('''\
    <?xml version="1.0" encoding="utf-8"?>
    <browserconfig>
        <msapplication>
            <tile>
                <square150x150logo src="/mstile-150x150.png"/>
                <TileColor>''' + theme_bg_hex + '''</TileColor>
            </tile>
        </msapplication>
    </browserconfig>
    ''')
    (direct_copy_path / 'site.webmanifest').write_text('''\
    {
        "name": "''' + name + '''",
        "short_name": "''' + name + '''",
        "icons": [
            {
                "src": "/android-chrome-192x192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/android-chrome-512x512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ],
        "theme_color": "''' + theme_fg_hex + '''",
        "background_color": "''' + theme_bg_hex + '''",
        "display": "browser"
    }
    ''')

    (templates_path / 'layout.html').write_text('''\
    {% extends "!layout.html" %}
    {% block extrahead %}
        <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
        <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
        <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
        <link rel="manifest" href="/site.webmanifest">
        <meta name="msapplication-TileColor" content="''' + theme_bg_hex + '''">
        <meta name="theme-color" content="''' + theme_fg_hex + '''">
    {% endblock %}
    ''')


def parse_rst(path: Path) -> docutils.nodes.document:
    parser = docutils.parsers.rst.Parser()
    settings = docutils.frontend.get_default_settings(docutils.parsers.rst.Parser)
    settings.report_level = docutils.utils.Reporter.SEVERE_LEVEL
    document = docutils.utils.new_document(path.name, settings=settings)
    parser.parse(path.read_text(), document)
    return document


def get_text(arg):
    rc = []
    for node in arg:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
        else:
            rc.append(get_text(node.childNodes))
    return ''.join(rc)


class Tag:
    all_tags = {}

    def __init__(self, slug, name):
        self.slug = slug
        self.name = name.strip()
        self.ref_name = 'tag-' + self.slug
        self.ref = f':bdg-ref-primary-line:`{self.name} <{self.ref_name}>`'
        self.nonref = f':bdg-primary-line:`{self.name}`'
        self.posts = []
        self.all_tags[self.slug] = self

    def __repr__(self):
        return f'<Tag: {self.name}>'

    def get_ref(self, draft):
        # Unknown refs can cause annoying warnings if left over
        return self.nonref if draft else self.ref

    @classmethod
    def get_or_create(cls, name):
        name = name.strip()
        slug = slugify(name)
        if slug in cls.all_tags:
            tag = cls.all_tags[slug]
        else:
            tag = Tag(slug, name)
        return tag

    @classmethod
    def process_tag_str(cls, post, tag_str):
        tags = []
        tag_str = tag_str.strip()
        if tag_str:
            for name in tag_str.split(','):
                tag = Tag.get_or_create(name)
                if tag not in tags:
                    tag.posts.append(post)
                    tags.append(tag)
        return tags

    @classmethod
    def get_sorted(cls, tags=None):
        return sorted(cls.all_tags.values() if tags is None else tags,
            key=lambda t: (-len(t.posts), t.name))


class Post:
    all_posts = []

    def __init__(self, path, title, doc_info, include_drafts=True):
        self.path = path
        self.title = title
        self.link = str(path.with_suffix(''))
        self.ref = f':doc:`/{self.link}`'
        self.draft = 'orphan' in doc_info
        self.summary = doc_info.get('summary')
        self.created = doc_info.get('created')
        if self.created is not None:
            self.created = datetime.fromisoformat(self.created)
        self.published = doc_info.get('published')
        if self.published is not None:
            self.published = datetime.fromisoformat(self.published)
        self.tags = []

        if self.draft and not include_drafts:
            return

        if 'tags' in doc_info:
            self.tags = Tag.process_tag_str(self, doc_info['tags'])

        self.all_posts.append(self)

    def tag_list(self, add_to):
        if self.tags:
            info.append('    :material-regular:`sell` ' +
                ' '.join([tag.ref for tag in self.tags]))

    def dt(self):
        if self.published is None:
            return self.created
        else:
            return self.published

    def post_info(self, for_post=False):
        i = '    '
        draft_post_warning = ':bdg-danger:`DRAFT POST`'
        info = []
        if for_post:
            if self.draft:
                info = ['.. danger:: ' + draft_post_warning, '']
            else:
                info = ['.. card::', '']
        else:
            title = self.ref
            if self.draft:
                title = title + ' ' + draft_post_warning
            info.append(title)
        if self.summary and not for_post:
            info.append(f'{i}*{self.summary}*\n')
        date = self.dt().date()
        info.append(f'{i}:material-regular:`calendar_month` {date}')
        if self.tags:
            info.append(i + ':material-regular:`sell` ' +
                ' '.join([tag.get_ref(self.draft) for tag in self.tags]))
        info.append('')
        return info

    @classmethod
    def get_years(cls, posts=None, year=None, reverse=True):
        years = set()
        for post in cls.all_posts:
            years |= {post.dt().year}
        return years

    @classmethod
    def get_sorted(cls, posts=None, year=None, reverse=True):
        posts = Post.all_posts if posts is None else posts
        if year is not None:
            posts = filter(lambda p: p.dt().year == year, posts)
        posts = sorted(posts, key=lambda p: p.title)
        return sorted(posts, key=lambda p: p.dt(), reverse=reverse)


def insert_into_file(path, marker, lines):
    rewrite_lines = True
    found_start = False
    found_end = False
    rewrite = []
    start_marker = '.. ' + marker + '-start'
    end_marker = '.. ' + marker + '-end'
    for line in path.read_text().split('\n'):
        if line == start_marker:
            if found_start or found_end:
                sys.exit(f'Invalid markers in {path}')
            found_start = True
            rewrite.append(line)
            rewrite.append('')
            rewrite.extend(lines)
            rewrite_lines = False
        elif line == end_marker:
            if not found_start or found_end:
                sys.exit(f'Invalid markers in {path}')
            found_end = True
            rewrite_lines = True
            rewrite.append('')
        if rewrite_lines:
            rewrite.append(line)
    if not found_start or not found_end:
        sys.exit(f'Invalid markers in {path}')
    path.write_text('\n'.join(rewrite))


def header(title):
    h = '#' * len(title) + '\n'
    return h + title + '\n' + h


def write_list_file(path, title, items=[], toc=[], ref=''):
    lines = [
        ':orphan:',
        '',
    ]
    if ref:
        lines.append(f'.. _{ref}:\n')
    lines.append(header(title))
    if toc:
        lines.append('.. toctree::')
        if items:
            lines.append('    :hidden:')
        lines.extend([
            '    :maxdepth: 1',
            '',
        ])
        for item in toc:
            lines.append('    ' + item)
        lines.append('')
    path.write_text('\n'.join(lines + items))


def load_posts(include_drafts=False, verbose=False):
    for path in posts_path.glob('*/*.rst'):
        if path.name == 'index.rst':
            continue
        if verbose:
            print(path)
        rst_doc = parse_rst(path)
        dom = rst_doc.asdom()

        # Get title
        title = None
        for title_node in dom.getElementsByTagName('title'):
            title = get_text([title_node])
            break
        if verbose:
            print(' ', title)
        if title is None:
            sys.exit('ERROR: post is missing title')

        # Get doc_info (metadata)
        doc_info = {}
        for field_list in dom.getElementsByTagName('field_list'):
            for field in field_list.childNodes:
                name = get_text(field.getElementsByTagName('field_name'))
                value = get_text(field.getElementsByTagName('field_body'))
                doc_info[name] = value

        post = Post(path, title, doc_info, include_drafts=include_drafts)
        if verbose:
            print(' ', post.link)
        if not post.draft and post.published is not None and post.path.parent.name != str(post.published.year):
            sys.exit(f'ERROR: post is in {post.path.parent.name}, but is marked {post.published.year}')
        if not post.draft:
            if post.created is None:
                sys.exit('ERROR: post to publish is missing created')
            if post.published is None:
                sys.exit('ERROR: post to publish is missing published')
            if not post.tags:
                sys.exit('ERROR: post to publish is missing tags')
            if not post.summary:
                sys.exit('ERROR: post to publish is missing summary')

        # Write post info back
        insert_into_file(path, 'post-info', post.post_info(for_post=True))


def new_post(title):
    load_posts(include_drafts=True)
    year_path = posts_path / str(now.year)
    year_path.mkdir(exist_ok=True)
    path = year_path / (slugify(title) + '.rst')
    if path.exists():
        sys.exit(f'{repr(title)} would go to {path}, which already exists!')

    path.write_text('\n'.join([
        f':created: {now}',
        ':orphan:',
        ':tags:',
        ':summary:',
        '',
        header(title),
        '',
        '.. post-info-start',
        '.. post-info-end',
        '',
        'Content goes here',
    ]))
    print('Created', path)


def publish_post(post_path):
    log(f'Publishing {post_path}')

    new_lines = [f':published: {now}']
    inspect_lines = True
    for line in post_path.read_text().split('\n'):
        write_line = True
        if inspect_lines:
            if line == ':orphan:' or line.startswith(':published'):
                write_line = False
            elif line == '.. post-info-start':
                inspect_lines = False
        if write_line:
            new_lines.append(line)
    post_path.write_text('\n'.join(new_lines))


def generate_blog(include_drafts):
    log('Generating content for blog (tags, recent posts, etc.)...')

    load_posts(include_drafts, verbose=True)

    # Write recent post lists to index.rst
    lines = []
    for post in Post.get_sorted()[:5]:
        lines.extend(post.post_info())
    insert_into_file(index_path, 'recent-posts', lines)

    # Write posts.rst
    posts_toc = []
    for year in sorted(Post.get_years(), reverse=True):
        year_path = posts_path / str(year)
        lines = []
        year_toc = []
        for post in Post.get_sorted(year=year, reverse=False):
            lines.extend(post.post_info())
            year_toc.append(post.path.name)
        write_list_file(year_path / 'index.rst', f'Posts in {year}', lines, toc=year_toc)
        posts_toc.append(f'{year} <{year}/index>')
    write_list_file(posts_path / 'index.rst', 'Posts', toc=posts_toc)

    # Write tags.rst
    if tags_path.is_dir():
        rmtree(tags_path)
    tags_path.mkdir()
    lines = []
    tags_toc = []
    for tag in Tag.get_sorted():
        lines.append(tag.ref + ' ' + str(len(tag.posts)) + ' post(s)')
        lines.append('')
        tags_toc.append(str(tags_path / tag.slug))
    write_list_file(tags_path.with_suffix('.rst'), 'Tags', lines, toc=tags_toc)

    # Write tags/*.rst
    for tag in Tag.all_tags.values():
        lines = []
        for post in Post.get_sorted(posts=tag.posts):
            lines.extend(post.post_info())
        write_list_file((tags_path / tag.slug).with_suffix('.rst'),
            tag.name, lines, ref=tag.ref_name)


class DocEnv:
    def __init__(self, venv_path, build_path, drafts):
        self.venv_path = Path(venv_path)
        self.abs_venv_path = self.venv_path.resolve()
        self.bin_path = self.abs_venv_path / 'bin'
        self.build_path = Path(build_path)
        self.abs_build_path = self.build_path.resolve()
        self.html_output = self.abs_build_path / 'html'
        self.drafts = drafts
        self.done = set()

    def run(self, *cmd, cwd=abs_root):
        env = os.environ.copy()
        env['VIRUTAL_ENV'] = str(self.abs_venv_path)
        env['PATH'] = str(self.bin_path) + os.pathsep + env['PATH']
        log('Running', repr(' '.join(cmd)), 'in', repr(str(cwd)))
        check_call(cmd, env=env, cwd=cwd)

    def rm_build(self):
        if self.build_path.is_dir():
            log('build.py: Removing existing {}...'.format(self.build_path))
            rmtree(self.build_path)

    def setup(self, force_new=False):
        sanity_path = self.bin_path / 'sphinx-build'
        install_deps = False
        if force_new or not self.venv_path.is_dir():
            log('Creating venv...')
            venv.create(self.venv_path, clear=True, with_pip=True)
            install_deps = True
        elif reqs_path.stat().st_mtime >= self.venv_path.stat().st_mtime:
            log('Requirements file was changed, updating dependencies.')
            install_deps = True
        elif not sanity_path.is_file():
            log('sphinx-build not found, need to install dependencies?')
            install_deps = True

        if install_deps:
            log('Install Dependencies...')
            self.run('python', '-m', 'pip', 'install', '-r', str(reqs_path))
            if not sanity_path.is_file():
                log('sphinx-build not found after installing dependencies', error=True)
                sys.exit(1)
            self.venv_path.touch()
            self.rm_build()

    def sphinx_build(self, builder, *args):
        args = list(args)
        self.run('sphinx-build', '-M', builder, '.', str(self.abs_build_path), *args)

    def do(self, actions, because_of=None, open_result=False):
        for action in actions:
            log('Doing', action, ('needed by ' + because_of) if because_of else '')
            if action in self.done:
                log(action, 'already done')
                continue
            result_path = getattr(self, 'do_' + action)()
            self.done |= {action,}
            if open_result:
                if result_path is None:
                    log('Can\'t open', action, 'result')
                else:
                    uri = result_path.as_uri()
                    log('Opening', uri)
                    webbrowser.open(uri)

    @classmethod
    def all_actions(cls):
        return [k[3:] for k, v in vars(cls).items() if k.startswith('do_')]

    def do_strict(self):
        self.sphinx_build('dummy', '-W')
        self.sphinx_build('linkcheck')
        return None

    def do_icons(self):
        generate_icons()

    def do_blog(self):
        generate_blog(self.drafts)
        return None

    def do_html(self):
        self.do(['blog'], because_of='html')
        self.sphinx_build('html')
        return self.html_output / 'index.html'

    def do_serve(self):
        self.do(['html'], because_of='serve')
        html_output = self.html_output
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kw):
                super().__init__(*args, directory=html_output, **kw)

        port = 8000
        with socketserver.TCPServer(("", port), Handler) as httpd:
            print(f'Serving http://127.0.0.1:{port}')
            httpd.serve_forever()


if __name__ == '__main__':
    arg_parser = ArgumentParser(description=__doc__)
    arg_parser.add_argument('--build',
        metavar='PATH', type=Path, default=default_build_path,
        help='Where to place the results. Default is %(default)s'
    )
    arg_parser.add_argument('--venv',
        metavar='PATH', type=Path, default=default_venv_path,
        help='Where to place the Python virtual environment. Default is %(default)s'
    )
    arg_parser.add_argument('--drafts',
        action='store_true',
        help='Include draft posts'
    )
    subcmds = arg_parser.add_subparsers(required=True, dest='subcmd')

    do_subcmd = subcmds.add_parser('do')
    do_subcmd.add_argument('actions', nargs='+', choices=DocEnv.all_actions())
    do_subcmd.add_argument('-o', '--open',
        action='store_true',
        help='Open result after building'
    )

    new_subcmd = subcmds.add_parser('new')
    new_subcmd.add_argument('title', metavar='TITLE')

    pub_subcmd = subcmds.add_parser('pub')
    pub_subcmd.add_argument('post_path', metavar='POST_PATH', type=Path)

    args = arg_parser.parse_args()
    doc_env = DocEnv(args.venv, args.build, drafts=args.drafts)
    doc_env.setup()
    if args.subcmd == 'do':
        doc_env.do(args.actions, open_result=args.open)
    elif args.subcmd == 'new':
        new_post(args.title)
    elif args.subcmd == 'pub':
        publish_post(args.post_path)
        doc_env.do(['html'])

# vim: expandtab:ts=4:sw=4
