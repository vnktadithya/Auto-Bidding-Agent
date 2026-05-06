import { useState, useEffect } from 'react'

function Settings({ apiBase, showToast }) {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  // Persona fields
  const [title, setTitle] = useState('')
  const [experience, setExperience] = useState('')
  const [coreStack, setCoreStack] = useState([])
  const [specialties, setSpecialties] = useState([])
  const [availability, setAvailability] = useState('')
  const [tone, setTone] = useState('')

  // Automation fields
  const [webhookUrl, setWebhookUrl] = useState('')

  // Keyword fields
  const [keywords, setKeywords] = useState([])

  // Temp inputs for adding tags
  const [stackInput, setStackInput] = useState('')
  const [specialtyInput, setSpecialtyInput] = useState('')
  const [keywordInput, setKeywordInput] = useState('')

  useEffect(() => {
    fetchConfig()
  }, [])

  const fetchConfig = async () => {
    try {
      const res = await fetch(`${apiBase}/config`)
      const data = await res.json()

      // Populate persona
      if (data.persona) {
        setTitle(data.persona.title || '')
        setExperience(data.persona.years_of_experience?.toString() || '')
        setCoreStack(data.persona.core_stack || [])
        setSpecialties(data.persona.specialties || [])
        setAvailability(data.persona.availability || '')
        setTone(data.persona.tone || '')
      }

      // Populate keywords
      if (data.keywords) {
        setKeywords(data.keywords.keywords || [])
      }

      // Populate webhook
      setWebhookUrl(data.webhook_url || '')
    } catch (err) {
      console.error('Failed to fetch config:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const payload = {
        persona: {
          title,
          years_of_experience: parseInt(experience) || 0,
          core_stack: coreStack,
          specialties,
          availability,
          tone
        },
        keywords: {
          keywords
        },
        webhook_url: webhookUrl
      }

      const res = await fetch(`${apiBase}/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (res.ok) {
        showToast('Configuration saved successfully!')
      } else {
        showToast('Failed to save configuration', 'error')
      }
    } catch (err) {
      showToast('Network error. Is FastAPI running?', 'error')
    } finally {
      setSaving(false)
    }
  }

  const addTag = (list, setList, input, setInput) => {
    const trimmed = input.trim()
    if (trimmed && !list.includes(trimmed)) {
      setList([...list, trimmed])
      setInput('')
    }
  }

  const removeTag = (list, setList, index) => {
    setList(list.filter((_, i) => i !== index))
  }

  const handleKeyDown = (e, list, setList, input, setInput) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      addTag(list, setList, input, setInput)
    }
  }

  if (loading) {
    return (
      <div className="empty-state">
        <div className="spinner" style={{ margin: '0 auto' }}></div>
        <p style={{ marginTop: '16px' }}>Loading configuration...</p>
      </div>
    )
  }

  return (
    <>
      <div className="page-header">
        <h2>⚙️ Configuration</h2>
        <p>Customize your bidding persona and search interests. Changes will be used in the next scraping cycle.</p>
      </div>

      {/* Persona Card */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-title">
          <span className="card-icon">👤</span>
          Persona Settings
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label className="form-label">Professional Title</label>
            <input
              type="text"
              className="form-input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Full-Stack Software Engineer"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Years of Experience</label>
            <input
              type="number"
              className="form-input"
              value={experience}
              onChange={(e) => setExperience(e.target.value)}
              placeholder="e.g., 2"
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Core Tech Stack</label>
          <input
            type="text"
            className="form-input"
            value={stackInput}
            onChange={(e) => setStackInput(e.target.value)}
            onKeyDown={(e) => handleKeyDown(e, coreStack, setCoreStack, stackInput, setStackInput)}
            placeholder="Type a technology and press Enter (e.g., Python)"
          />
          <p className="form-hint">Press Enter to add each technology.</p>
          <div className="tags-container">
            {coreStack.map((tag, i) => (
              <span key={i} className="tag">
                {tag}
                <button className="tag-remove" onClick={() => removeTag(coreStack, setCoreStack, i)}>×</button>
              </span>
            ))}
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Specialties</label>
          <input
            type="text"
            className="form-input"
            value={specialtyInput}
            onChange={(e) => setSpecialtyInput(e.target.value)}
            onKeyDown={(e) => handleKeyDown(e, specialties, setSpecialties, specialtyInput, setSpecialtyInput)}
            placeholder="Type a specialty and press Enter (e.g., Web Scraping)"
          />
          <p className="form-hint">Press Enter to add each specialty.</p>
          <div className="tags-container">
            {specialties.map((tag, i) => (
              <span key={i} className="tag">
                {tag}
                <button className="tag-remove" onClick={() => removeTag(specialties, setSpecialties, i)}>×</button>
              </span>
            ))}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label className="form-label">Availability</label>
            <input
              type="text"
              className="form-input"
              value={availability}
              onChange={(e) => setAvailability(e.target.value)}
              placeholder="e.g., Immediate"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Tone</label>
            <input
              type="text"
              className="form-input"
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              placeholder="e.g., Professional, confident, conversational"
            />
          </div>
        </div>
      </div>

      {/* Keywords Card */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-title">
          <span className="card-icon">🔍</span>
          Search Interests
        </div>

        <div className="form-group">
          <label className="form-label">Search Keywords</label>
          <input
            type="text"
            className="form-input"
            value={keywordInput}
            onChange={(e) => setKeywordInput(e.target.value)}
            onKeyDown={(e) => handleKeyDown(e, keywords, setKeywords, keywordInput, setKeywordInput)}
            placeholder='Type a search phrase and press Enter (e.g., "looking for AI engineer")'
          />
          <p className="form-hint">
            These phrases will be joined with OR logic on X and LinkedIn.
            Press Enter to add each one.
          </p>
          <div className="tags-container">
            {keywords.map((tag, i) => (
              <span key={i} className="tag">
                {tag}
                <button className="tag-remove" onClick={() => removeTag(keywords, setKeywords, i)}>×</button>
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Automation Card */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-title">
          <span className="card-icon">⚡</span>
          Automation Settings
        </div>

        <div className="form-group">
          <label className="form-label">n8n Production Webhook URL</label>
          <input
            type="text"
            className="form-input"
            value={webhookUrl}
            onChange={(e) => setWebhookUrl(e.target.value)}
            placeholder="http://localhost:5678/webhook/..."
          />
          <p className="form-hint">
            This URL is used to trigger the bot manually from the Activity Log. 
            Use your <strong>Production URL</strong> from n8n.
          </p>
        </div>
      </div>

      {/* Save Button */}
      <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
        {saving ? (
          <>
            <div className="spinner"></div>
            Saving...
          </>
        ) : (
          <>💾 Save Configuration</>
        )}
      </button>
    </>
  )
}

export default Settings
