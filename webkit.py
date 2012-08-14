#!/usr/bin/python

import re
import subprocess

def parse_log(since='2 years ago',until='today'):
    """Parse the commit log, yielding (date, author email) pairs.

    Parser is WebKit-aware: it knows the committer frequently isn't
    the author.

    |since| is an argument for the --since flag to git log.
    """

    commit_re = re.compile('^commit ')
    author_re = re.compile('^Author: .*<([^@]+@[^@]+).*>')
    date_re = re.compile('^Date:\s+(\S+)')
    topics_re = re.compile('^    ((?:\[\w+\])+)')
    # Regexp for a ChangeLog header: date + author name + author email.
    changelog_re = re.compile('^    \d\d\d\d-\d\d-\d\d  .+?  <(.+?)>')
    # Regexp for a in-ChangeLog commit message.
    patch_re = re.compile('^    Patch by .+? <([^@]+@[^@]+).*> on \d\d\d\d-\d\d-\d\d')

    log = subprocess.Popen(['git', 'log', '--date=short', '--since=' + since,'--until=' + until],
                           stdout=subprocess.PIPE)
    n = 0
    for line in log.stdout.xreadlines():
        if commit_re.match(line):
            if n > 0:
                if ' and ' in author:
                    author = author[0:author.find(' and ')]
                yield date, author, topics
            author = None
            date = None
            topics = None
            n += 1
            continue
        match = author_re.match(line)
        if match:
            author = match.group(1)
            continue
        match = date_re.match(line)
        if match:
            date = match.group(1)
            continue
        match = topics_re.match(line)
        if match:
			topics = re.findall("\w+",match.group(1))
			continue
        match = changelog_re.match(line)
        if match:
            author = match.group(1)
            continue
        match = patch_re.match(line)
        if match:
            author = match.group(1)
            continue

# See:  http://trac.webkit.org/wiki/WebKit%20Team

# Mapping of domain name => company name.
domain_companies = {
    'chromium.org': 'google',
    'google.com': 'google',
    'chromium.com': 'google',
    'apple.com': 'apple',
    'igalia.com': 'igalia',
    'nokia.com': 'nokia',
    # trolltech was acquired by nokia.
    'trolltech.com': 'nokia',
    # torch was acquired by RIM.
    'torchmobile.com.cn': 'rim',
    'torchmobile.com': 'rim',
    'rim.com': 'rim',
    'appcelerator.com': 'appcelerator',
    # u-szeged.hu is a university team working on WebKit on behalf of Nokia.
    'inf.u-szeged.hu': 'nokia',
    'stud.u-szeged.hu': 'nokia',
    'ericsson.com': 'ericsson',
    # openbossa seems to be nokia; from their about page
    # "Open Bossa is the response of Nokia Technology Institute to ..."
    'openbossa.org': 'nokia',
    'openbossa.com': 'nokia',
    # Seems to be contracting for Nokia on the Symbian port.
    'digia.com': 'nokia',
    'collabora.co.uk': 'collabora',
    'collabora.com': 'collabora',
    'sencha.com': 'sencha',
    'profusion.mobi': 'samsung', # Samsung subcontractors.
    'samsung.com': 'samsung',
	'sisa.samsung.com': 'samsung',
	'intel.com': 'intel',
	'linux.intel.com': 'intel',
	'adobe.com': 'adobe',
	'motorola.com': 'motorola',
	'company100.net': 'company100',
	'orange.com': 'orange',
	'orange.fr': 'orange',
	'softathome.com': 'orange'
}

# Lists of particular names known to be in some companies.
other = {
    'google': [
        'abarth@webkit.org',
        'eric@webkit.org',
        'christian.plesner.hansen@gmail.com',  # v8
        'joel@jms.id.au',  # intern
        'rniwa@webkit.org',  # intern
        'shinichiro.hamaji@gmail.com',
        'scarybeasts@gmail.com',
		'jchaffraix@webkit.org',
		'noel.gordon@gmail.com',
		'keishi@webkit.org',
		'dkilzer@webkit.org',
		'eustas.bug@gmail.com' # Eugene Klyuchnikov
    ],

    'apple': [
        'ap@webkit.org',
        'sam@webkit.org',
		'weinig@webkit.org',
        'joepeck@webkit.org',
		'jberlin@webkit.org',
		'mitz@webkit.org',
		'ddkilzer@webkit.org'
    ],

    'redhat': [
        'danw@gnome.org',
        'otte@webkit.org',
    ],

    'nokia': [
        'hausmann@webkit.org',
        'kenneth@webkit.org',
        'tonikitoo@webkit.org',
        'vestbo@webkit.org',
        'girish@forwardbias.in',  # Appears to be consulting for Qt = Nokia(?).
        'benjamin@webkit.org',
        'kling@webkit.org',
        'kbalazs@webkit.org',
        'ossy@webkit.org',
        'zherczeg@webkit.org',
        'abecsi@webkit.org',
        'diegohcg@webkit.org',
        'loki@webkit.org',
        'kim.gronholm@nomovok.com' # Nokia subcontractor,
		'cmarcelo@webkit.org',
		'reni@webkit.org', # Member of szeged
		'rgabor@webkit.org', # Member of szeged
		'zeno@webkit.org',
		'zbujtas@gmail.com',
		'pierre.rossi@gmail.com',
		'ahf@0x90.dk',
		'jesus@webkit.org'
    ],

    'rim': [
        'dbates@webkit.org',
        'zimmermann@webkit.org',
        'krit@webkit.org',
		'rwlbuis@webkit.org',
		'cmarcelo@webkit.org'
    ],
    
    'qualcomm': [
		'dtharp@codeaurora.org',
		'tomz@codeaurora.org'
	],
	
	'HP Palm': [
		'luiz@webkit.org'
	],

    'misc': [
        'bfulgham@webkit.org',  # WinCairo
        'cjerdonek@webkit.org',  # Random script/style cleanups?
        'jmalonzo@unpluggable.com',  # GTK
        'joanmarie.diggs@gmail.com',  # GTK Accessibility (Sun?)
        'simon.maxime@gmail.com',  # Haiku
        'skyul@company100.net',  # BREWMP
        'zandobersek@gmail.com',  # GTK
        'zecke@webkit.org',  # GTK+Qt
        'christian@twotoasts.de',  # GTK, Midori

        'alp@atoker.com',  # Did a lot of the GTK port for a company.

        # A post by him on a mailing list had Arora in the code snippet.
        'robert@webkit.org',  # Qt, Arora

		'jwieczorek@webkit.org', # Arora

        'cam@mcc.id.au',  # SVG

        'paroga@webkit.org',  # WinCE
		'robert@webkit.org', # torora

        # Inspector attracts all sorts of random hackers:
        'joepeck@webkit.org',
        'Patrick_Mueller@us.ibm.com',
        'casey.hattori@gmail.com',
        
        # Mathml
        'dbarton@mathscribe.com',
        # Security
        'serg.glazunov@gmail.com',
        # ??
        'dobey@wayofthemonkey.com',
        'peter.rybin@gmail.com',
        'alex@milowski.com'
    ],

    'samsung': [
        'rakuco@webkit.org',
		'cshu@webkit.org',
		'igor.oliveira@webkit.org',
		'vivekgalatage@gmail.com' # Was at Nokia 
    ],
    
    'netflix': [
		'agbakken@gmail.com'
	],
	
	'sencha': [
		'ariya@webkit.org'
	],
    
    'bots': [
		'webkit.review.bot@gmail.com'
	]

}

# One-off mapping of names to companies.
people_companies = {
    'mrobinson@webkit.org': 'appcelerator',
    'xan@gnome.org': 'igalia',
    'kevino@webkit.org': 'wx',
    'gns@gnome.org': 'collabora'
}


email_sets = [
    ['xan@gnome.org', 'xan@webkit.org'],
    ['kevino@webkit.org', 'kevino@theolliviers.com'],
    ['gns@gnome.org', 'gustavo.noronha@collabora.co.uk', 'kov@webkit.org'],
    ['ariya@webkit.org', 'ariya.hidayat@gmail.com'],
    ['mbelshe@chromium.org', 'mike@belshe.com'],
    ['joepeck@webkit.org', 'joepeck02@gmail.com'],
    ['zecke@webkit.org', 'zecke@selfish.org'],
    ['dbates@webkit.org', 'dbates@intudata.com'],
    ['tonikitoo@webkit.org', 'antonio.gomes@openbossa.org'],
    ['kenneth@webkit.org', 'kenneth.christiansen@openbossa.org'],
    ['otte@webkit.org', 'otte@gnome.org'],
    ['abarth@webkit.org', 'abarth'],
    ['finnur@chromium.org', 'finnur.webkit@gmail.com'],
    ['atwilson@chromium.org', 'atwilson@atwilson-macpro.local'],
    ['mrobinson@webkit.org', 'martin.james.robinson@gmail.com'],
    ['kinuko@chromium.org', 'kinuko@chromium.com'],
    ['antonm@chromium.org', 'antonm@chromium'],
    ['snej@chromium.org', 'jens@mooseyard.com'],
    ['yaar@chromium.org', 'yaar@chromium.src'],
    ['trungl@chromium.org', 'viettrungluu@gmail.com'],
    ['oszi@inf.u-szeged.hu', 'ossy@webkit.org'],
    ['hzoltan@inf.u-szeged.hu', 'horvath.zoltan.6@stud.u-szeged.hu',
     'zoltan@webkit.org'],
    ['pvarga@inf.u-szeged.hu','pvarga@webkit.org'],
    ['jmalonzo@unpluggable.com', 'jmalonzo@webkit.org'],
    ['krit@webkit.org', 'vbs85@gmx.de'],
    ['cjerdonek@webkit.org', 'chris.jerdonek@gmail.com'],
    ['zwarich@apple.com', 'cwzwarich@uwaterloo.ca'],
    ['alp@atoker.com', 'alp@nuanti.com', 'alp@webkit.org'],
    ['treat@rim.com', 'treat@webkit.org','treat@kde.org'],
    ['rniwa@webkit.org', 'ryosuke.niwa@gmail.com'],
    ['christian@twotoasts.de', 'christian@webkit.org', 'christian@twoasts.de'],
    ['george.staikos@torchmobile.com', 'staikos@kde.org', 'staikos@webkit.org'],
    ['kuchhal@chromium.org', 'kuchhal@yahoo.com'],
    ['benjamin@webkit.org', 'ikipou@gmail.com'],
    ['zherczeg@webkit.org', 'hzoltan@inf.u-szeged.hu', 'horvath.zoltan.6@stud.u-szeged.hu'],
    ['abecsi@webkit.org', 'becsi.andras@stud.u-szeged.hu', 'abecsi@inf.u-szeged.hu'],
    ['krit@webkit.org', 'vbs85@gmx.de'],
    ['weinig@webkit.org', 'sam@webkit.org'],
    ['paroga@webkit.org', 'paroga@paroga.com'],
    ['bfulgham@webkit.org', 'bfulgham@gmail.com'],
    ['zimmermann@webkit.org', 'zimmermann@kde.org'],
    ['jwieczorek@webkit.org', 'faw217@gmail.com'],
    ['robert@webkit.org', 'robert@roberthogan.net'],
    ['kevin.cs.oh@gmail.com','shivamidow@gmail.com'],
    ['jpfau@apple.com','jeffrey@endrift.com'],
    ["rwlbuis@webkit.org", "rwlbuis@gmail.com", "rbuis@rim.com"],
    ["mlilek@apple.com", "webkit@mattlilek.com", "pewtermoose@webkit.org"]
]
canon_map = {}
for emails in email_sets:
    for email in emails[1:]:
        canon_map[email] = emails[0]

def canonicalize_email(author_email):
    """Return a generic email address for author using various email address."""
    if author_email in canon_map:
        return canon_map[author_email]
    return author_email


def classify_email(email):
    """Given an email, return a string identifying their company."""
    domain = None
    if '@' in email:
        _, domain = email.split('@')
    if domain:
        if domain in domain_companies:
            return domain_companies[domain]
        if domain.endswith('.google.com'):
            return 'google'
    if email in people_companies:
        return people_companies[email]

    for company, people in other.iteritems():
        if email in people:
            return company

    if not domain:
        # Before they started using email addresses, they just had
        # usernames.  Assume this means Apple.
        return 'apple'

    return 'unknown'
