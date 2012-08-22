#!/usr/bin/python

import re
import subprocess

def parse_log(since='2 years ago',until='today'):
    """Parse the commit log, yielding (date, author email) pairs.

    Parser is WebKit-aware: it knows the committer frequently isn't
    the author.

    |since| is an argument for the --since flag to git log.
    """

    blank_re = re.compile("^\s*$")
            
    commit_re = re.compile('^commit (\w+)')
    committer_re = re.compile('^Author: .*<([^@]+@[^@]+).*>')
    date_re = re.compile('^Date:\s+(\S+)')
    
    # Regexp for a ChangeLog header: date + author name + author email.
    changelog_re = re.compile('^    \d\d\d\d-\d\d-\d\d  .+?  <(.+?)>')
    # Regexp for a Reviewed By message
    reviewed_re = re.compile('^\s+(?:(?:Reviewed|Rubber-stamped|Rubber stamped|Rubberstamped|Suggested)\sby\s+([\w\s]+)|(Unreviewed)\.)',re.IGNORECASE)
    # Regexp for a in-ChangeLog commit message.
    patch_re = re.compile('^    Patch by .+? <([^@]+@[^@]+).*> on \d\d\d\d-\d\d-\d\d')
    
    # Regexp to identify single rdar:: lines
    rdar_re = re.compile("^\s+<rdar\://[\w/]+>\s*$")
    
    # Regexp to identify single show_bug.cgi lines
    show_bug_re = re.compile("^\s+https\://bugs\.webkit\.org\/show_bug\.cgi\?id\=[\d]+\s*$")
    
    # Regexp for description headers
    headers_re = re.compile('^\s+(?:\.\./)*(?:Volumes/Data/git/WebKit/OpenSource)?(?:Source/)?(?:WebKit/)?(?:platform/)?(?:ThirdParty/)?([\w]+)/?\:$')

    # Regexp for platform specific modified files
    #platform_re = re.compile('^\s+\*\s(?:platform|plugins|history|editing|bridge|accessibility)/(?:graphics/)?(?:network/)?(\w+)/')
    filepath_re = re.compile('^\s+\*\s((?:[\w]+/)*)(\w+)\.(\w+)')
    
    # Regexp for the end of commit
    end_re = re.compile('^\s+git-svn-id')

    log = subprocess.Popen(['git', 'log', '--date=short', '--since=' + since,'--until=' + until],
                           stdout=subprocess.PIPE)
    
    # We can have one of the two following log templates:
    # A - Git Header, Changelog, (Reviewed by|Subject), Description, Files
    # B - Git Header Subject, Reviewed by, Description, Files
    # (where Git header is commit/committer/date)
    
    insubject = False
    for line in log.stdout.xreadlines():
        # We skip blank lines and use them to separate blocks
        if blank_re.match(line):
            if insubject:
				topics = identify_keywords(subject)
            insubject = False
            continue
        # We also skip single rdar:: lines
        if rdar_re.match(line):
            continue
        # And single show_bug.cgi lines
        if show_bug_re.match(line):
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
            #   print subject
            yield date, author, topics        
            continue   
        # Start of commit 
        match = commit_re.match(line)
        if match: 
            commit = match.group(1)
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
        match = patch_re.match(line)
        if match:
            author = match.group(1)
            continue
        # If we went this far we should have identified the commit
        # subject and isolated topics
        if topics:
            continue
        # If not, parse the description for headers
        match = headers_re.match(line)
        if match:
            topic = match.group(1).lower()
            if topic in canon_topic_map:
                if topics == None:
                    topics = []
                topics.append(match.group(1))
            continue
        # And parse the modified files
        match = filepath_re.match(line)
        if match:
            topic_found = False
            directories = match.group(1)
            filename = match.group(2)
            extension = match.group(3)
            if filename:
                patterns = identify_keywords(filename)
                if patterns:
                    topic_found = True
                    if topics == None:
                        topics = []
                    topics.extend(patterns)
            if topic_found:
                continue        
            if directories:
                directories = re.split("/",match.group(1))
                directories.reverse()
                for directory in directories:
                    topic = directory.lower()
                    if topic in canon_topic_map:
                        if topics == None:
                            topics = []
                        topic_found = True
                        topics.append(topic)
                        break
            if not topic_found:
                if extension in mac_extensions:
                    topics.append("mac")
                    topic_found = True
                elif extension in qt_extensions:
                    topics.append("qt")
                    topic_found = True
                elif extension in gtk_extensions:
                    topics.append("gtk")
                    topic_found = True
                elif extension in gnu_extensions:
                    topics.append("autotools")
                    topic_found = True
                elif extension in chromium_extensions:
                    topics.append("chromium")
                    topic_found = True
                elif extension in source_extensions:
                    for directory in directories:
                        if directory in webcore_directories:
                            if topics == None:
                                topics = []
                            topic_found = True
                            topics.append("webcore")
                            break
                        elif directory in javascriptcore_directories:
                            if topics == None:
                                topics = []
                            topic_found = True
                            topics.append("javascriptcore")
                            break                          
            #if not topics and not topic_found:
            #    print "Not found" + line
            continue       

def identify_keywords(text=''):
           
    # Identify keywords in a text
    
    # We first look for our "unambiguous" keywords
    keywords = unambiguous_tags_re.findall(text)
                
    # Then try the "ambiguous" ones
    if not keywords:
		keywords = ambiguous_tags_re.findall(text)
              
    # Then try to identify build fixes      
    if not keywords: 
        if build_fix_re.match(text):
            keywords = ['build fix']
                            
    return keywords

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
    ['chromium', 'chromium-mac', 'chromium-android', 'chromium-win', 'chrome', 'skia', 'angle', 'v8', 'gyp'],
    ['gtk', 'gtk2', 'cairo', 'soup', 'gstreamer', 'gdk'],
    ['qt', 'qtwebkit'],
    ['win', 'wince', 'windows', 'wincairo'],
    ['jsc', 'javascriptcore', 'yarr', 'dfg', 'kjs'],
    ['tools', 'webkittools', 'garden-o-matic', 'webkit-patch', 'build-webkit', 'webkitpy', 'dumprendertree', 'ews', 'layouttestcontroller', 'testrunner', "scripts", "webkittestrunner", "buildslavesupport" ],
    ['tests', 'test', 'layouttest', 'layouttests' , 'performancetests' ],
    ['wk2', 'webkit2', 'uiprocess', 'webprocess', 'pluginprocess'],
    ['wx'],
    ['efl', 'ewk'],
    ['cg'],
    ['qnx'],
    ['ax'],
    ['regression'],
    ['blackberry'],
    ['webcore'],
    ['webkit'],
    ['wtf'],
    ['texmap', 'texturemapper', 'texmapgl'],
    ['webgl'],
    ['webinspector', 'web inspector', 'inspector', 'drosera'],
    ['css', 'css2', 'css3' ],
    ['wml'],
    ['svg'],
    ['autotools', 'gnumake'],
    ['cmake'],
    ['nrwt'],
    ['openvg'],
    ['indexeddb'],
    ['websocket'],
    ['file api', 'filesystem api'],
    ['forms'],
    ['webaudio'],
    ['brewmp'],
    ['maintenance', 'deps', 'rolling out', 'roll out', 'rollout', 'refactoring', 'rebaseline', 'gardening' , 'expectations' , 'testexpectations' , 'build fix', 'buildfix', 'bump', 'versioning', 'changelog', 'typo', 'git', 'svn', 'subversion'],
    ['webkit team', 'committers', 'contributors', 'contributor'],
    ['webkitsite'],
    ['plugins']
]

mac_extensions =  ["mm","xcodeproj", "vcproj", "xconfig"]
qt_extensions = [ "pro", "pri" ]
gtk_extensions = [ "po" ]
chromium_extensions = [ "gyp" ]
source_extensions = [ "cpp", "h", "idl", "rb", "asm"]
gnu_extensions = [ 'ac', 'am', 'in' ]

webcore_directories = [ 
    "accessibility", 
    "css",
    "fileapi",
    "icu",
    "Modules",
    "rendering",
    "testing",
    "workers",
    "bindings",
    "dom",
    "ForwardingHeaders",
    "inspector",
    "page",
    "Resources",
    "xml",
    "bridge",
    "editing",
    "history",
    "loader",
    "platform",
    "storage",
    "html",
    "mathml",
    "plugins",
    "svg"
]

javascriptcore_directories = [
    "API",
    "bytecode",
    "dfg",
    "heap",
    "interpreter",
    "jit",
    "offlineasm",
    "parser",
    "runtime",
    "yarr",
    "assembler",
    "bytecompiler",
    "debugger",
    "disassembler",
    "ForwardingHeaders",
    "icu",
    "os-win32",
    "profiler",
    "shell",
    "tools",
    "llint"
]

ambiguous_topics = ["webkit","mac","win","windows","test"]

# Prepare regexp(s) to identify topic names
unambiguous_topics_re_str =""
ambiguous_topics_re_str=""

# Gather topic names
for topics in topic_sets:
    for topic in topics:
        if topic in ambiguous_topics:
            if ambiguous_topics_re_str == "":
                ambiguous_topics_re_str = "\W(" + topic
            else:
                ambiguous_topics_re_str = ambiguous_topics_re_str + "|" + topic
        else:
            if unambiguous_topics_re_str == "":
                unambiguous_topics_re_str = "(" + topic
            else:
                unambiguous_topics_re_str = unambiguous_topics_re_str + "|" + topic

if unambiguous_topics_re_str != "":
    unambiguous_topics_re_str = unambiguous_topics_re_str + ")"
if ambiguous_topics_re_str != "":
    ambiguous_topics_re_str = ambiguous_topics_re_str + ")\W"
    
unambiguous_tags_re = re.compile(unambiguous_topics_re_str,re.IGNORECASE)
ambiguous_tags_re = re.compile(ambiguous_topics_re_str,re.IGNORECASE)

# Regexp to identify build fixes
build_fix_re = re.compile("^.*((fix.*(build|compilation|warning))|((build|compilation|warning).*fix))",re.IGNORECASE)
        
canon_topic_map = {}
for topics in topic_sets:
    for topic in topics:
        canon_topic_map[topic] = topics[0]

def canonicalize_topic(topic):
    """Return a generic topic for close devts"""
    if topic in canon_topic_map:
        return canon_topic_map[topic]
    return topic

def enum(**enums):
    return type('Enum', (), enums)
