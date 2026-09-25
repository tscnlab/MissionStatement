-- Layout adapted from tscnlab/Projects; relative links also work on GitHub
-- project Pages under /MissionStatement/ and in a downloaded HTML file.
local function raw(value) return pandoc.RawBlock('html', value) end
function Pandoc(doc)
  if not FORMAT:match('html') then return doc end
  local comparison = quarto.doc.input_file:match('compare%.qmd$')
  local current = comparison and '' or ' aria-current="page"'
  local compare = comparison and ' aria-current="page"' or ''
  local header = '<a class="skip-link" href="#page-content">Skip to content</a>'
    .. '<header class="site-header"><a class="brand" href="index.html" aria-label="TSCN mission statement">'
    .. '<img src="assets/tscn-logo.png" width="7660" height="1451" alt="Translational Sensory &amp; Circadian Neuroscience Unit (MPS/TUM/TUMCREATE)"></a>'
    .. '<nav class="site-nav" aria-label="Main navigation"><ul class="nav-list" role="list">'
    .. '<li><a href="index.html"' .. current .. '>Mission statement</a></li>'
    .. '<li><a href="compare.html"' .. compare .. '>Compare versions</a></li>'
    .. '<li><a href="https://join.tscnlab.org/">Join the unit</a></li></ul></nav></header>'
  local footer = '<footer class="site-footer"><p>Translational Sensory &amp; Circadian Neuroscience Unit (MPS/TUM/TUMCREATE)</p>'
    .. '<div class="footer-links"><a href="https://github.com/tscnlab/MissionStatement">Source on GitHub</a>'
    .. '<a href="https://tscnlab.org/">Unit website</a></div></footer>'
  local result = pandoc.List({raw(header), raw('<div id="page-content" tabindex="-1" class="' .. (comparison and 'comparison-page' or 'text-page mission-page') .. '">')})
  result:extend(doc.blocks)
  result:insert(raw('</div>'))
  result:insert(raw(footer))
  doc.blocks = result
  return doc
end
