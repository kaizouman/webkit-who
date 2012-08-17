#!/usr/bin/python

import re
import subprocess

def parse_log(since='2 years ago',until='today'):
    """Parse the commit log, yielding (date, author email) pairs.

    Parser is WebKit-aware: it knows the committer frequently isn't
    the author.

    |since| is an argument for the --since flag to git log.
    """

    commit_re = re.compile('^commit (\w+)')
    committer_re = re.compile('^Author: .*<([^@]+@[^@]+).*>')
    date_re = re.compile('^Date:\s+(\S+)')
    
    # Regexp for a ChangeLog header: date + author name + author email.
    changelog_re = re.compile('^    \d\d\d\d-\d\d-\d\d  .+?  <(.+?)>')
    # Regexp for a Reviewed By message
    reviewed_re = re.compile('^\s+(?:Reviewed|Rubber-stamped|Rubber stamped|Suggested)\sby\s+([\w\s]+)')
    # Regexp for a in-ChangeLog commit message.
    patch_re = re.compile('^    Patch by .+? <([^@]+@[^@]+).*> on \d\d\d\d-\d\d-\d\d')
    
    # Regexp for tags inserted as change headers in the patch details
    tags_d_re = re.compile('^\s+(?:\.\./)*(?:Source/)?(?:WebKit/)?(?:platform/)?(?:ThirdParty/)?([\w/]+)\:(?![/\:])')
    # Regexp for platform specific modified files
    platform_re = re.compile('^\s+\*\s(?:platform|plugins|history|editing|bridge|accessibility)/(?:graphics/)?(?:network/)?(mac|qt|gtk|chromium|wx|win|wince|efl|blackberry)/')
    
    # Regexp for the end of commit
    end_re = re.compile('^\s+git-svn-id')

    log = subprocess.Popen(['git', 'log', '--date=short', '--since=' + since,'--until=' + until],
                           stdout=subprocess.PIPE)
    
    # We can have one of the two following log templates:
    # A - Git Header, Changelog, (Reviewed by|Subject), Description, Files
    # B - Git Header Subject, Reviewed by, Description, Files
    # (where Git header is commit/committer/date) 
    Templates = enum(UNKNOWN=0,A=1,B=2)
    
    insubject = False
    for line in log.stdout.xreadlines():
        # We skip blank lines and use them to separate blocks
        if re.match("^\s*$",line):
            if insubject:
                # Parse the subject for relevant topics
                topics = unambiguous_tags_re.findall(subject)
                if not topics:
                    topics = ambiguous_tags_re.findall(subject)
                    if not topics: 
						if build_fix_re.match(subject):
							topics = ['build fix']
            insubject = False
            continue
        # End of commit
        match = end_re.match(line)
        if match:
            if not author:
                author = committer
            if ' and ' in author:
                author = author[0:author.find(' and ')]
                if topics:
                    # Convert to lower case and remove duplicates
                    d = {}
                    for x in topics:
                        d[x.lower()] = 1
                    topics = list(d.keys())
            #if not topics:
            #    print subject
            yield date, author, topics          
            continue   
        # Start of commit 
        match = commit_re.match(line)
        if match: 
            commit = match.group(1)
            template = Templates.UNKNOWN
            committer = None
            date = None
            author = None
            subject = ""
            reviewer = None
            topics = None
            continue
        if commit:
            match = committer_re.match(line)
            if match:
                committer = match.group(1)
                continue
        if committer:
            match = date_re.match(line)
            if match:
                date = match.group(1)
                continue
        if date and not insubject:
            match = changelog_re.match(line)
            if match:
                author = match.group(1)
                continue
            else:
                match = reviewed_re.match(line)
                if match:
                    reviewer = match.group(1)
                    continue
                elif subject=="":
                    insubject = True
        if insubject:
            match = re.match("^(.*)$",line)
            subject = subject + match.group(1)
            continue
        # If we went this far we have reached the description
        match = patch_re.match(line)
        if match:
            author = match.group(1)
            continue
        match = tags_d_re.match(line)
        if match:
            if topics == None:
                topics = []
            topic = match.group(1)
            topics.append(match.group(1))
            continue
        match = platform_re.match(line)
        if match:
            if topics == None:
                topics = []
            topic = match.group(1)
            if topics.count(topic) == 0:
                topics.append(topic)
            continue       

def parse_subject(subject=''):
           
    # Regexp to identify unambiguous topic names
    tags_re = re.compile(topics_re_str,re.IGNORECASE)

    return unambiguous_tags_re.findall(subject)

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


topic_sets = [
    ['mac', 'safari', 'leopard', 'lion'],
    ['chromium', 'chromium-mac', 'chromium-android', 'chromium-win', 'chrome', 'skia', 'angle', 'v8'],
    ['gtk', 'gtk2', 'cairo', 'soup', 'gstreamer'],
    ['qt', 'qtwebkit'],
    ['win', 'wince', 'windows', 'wincairo'],
    ['jsc', 'javascriptcore'],
    ['tools', 'webkittools' ],
    ['tests', 'test', 'layouttest', 'layouttests' , 'performancetests' ],
    ['wk2', 'webkit2'],
    ['wx'],
    ['efl'],
    ['regression'],
    ['blackberry'],
    ['webcore'],
    ['texmap', 'texturemapper'],
    ['webinspector', 'web inspector'],
    ['css', 'css2', 'css3' ],
    ['cmake'],
    ['nrwt'],
    ['indexeddb'],
    ['maintenance', 'rolled deps', 'rolling out', 'refactoring', 'rebaseline', 'gardening' , 'expectations' , 'testexpectations' , 'build fix', 'bump', 'versioning', 'changelog']
]

# Prepare a regexp to identify non ambiguous topic names
topics_re_str =""

# Gather topic names
for topics in topic_sets:
    for topic in topics:
        # Some tags are too ambiguous
        if topic not in ["mac","windows"]:
            if topics_re_str == "":
                topics_re_str = "[\[\s/](" + topic
            else:
                topics_re_str = topics_re_str + "|" + topic
if topics_re_str != "":
    topics_re_str = topics_re_str + ")[\]\s\.\:,\(/\+]"

# Regexp to identify unambiguous topic names
unambiguous_tags_re = re.compile(topics_re_str,re.IGNORECASE)

# Regexp to identify ambiguous topic names
ambiguous_tags_re = re.compile("[\[\s/](mac|windows)[\]\s\.\:,\(/]",re.IGNORECASE)

# Regexp to identify build fixes
build_fix_re = re.compile("^.*(fix.*(build|compilation))|((build|compilation).*fix)",re.IGNORECASE)
#build_fix_re = re.compile("^.*(fix)",re.IGNORECASE)
        
canon_topic_map = {}
for topics in topic_sets:
    for topic in topics[1:]:
        canon_topic_map[topic] = topics[0]

def canonicalize_topic(topic):
    """Return a generic topic for close devts"""
    if topic in canon_topic_map:
        return canon_topic_map[topic]
    return topic

def enum(**enums):
    return type('Enum', (), enums)
