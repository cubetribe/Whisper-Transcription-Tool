# ❓ LLM Text Correction - Frequently Asked Questions

**Comprehensive FAQ for LeoLM text correction in Whisper Transcription Tool**

---

## 🚀 Getting Started

### Q: What is LeoLM and why is it used?

**A:** LeoLM is a 13-billion parameter German language model developed by Hessian.AI. It's specifically trained and optimized for German text understanding and generation, making it ideal for correcting German transcriptions. Unlike cloud-based solutions, LeoLM runs completely locally on your Mac, ensuring privacy and avoiding API costs.

**Key advantages:**
- ✅ **German-native**: Trained specifically for German language
- ✅ **Privacy**: All processing happens locally
- ✅ **No costs**: No API fees or subscription required
- ✅ **Offline**: Works without internet connection
- ✅ **Quality**: 13B parameters provide high-quality corrections

### Q: What are the system requirements?

**A:**
**Minimum requirements:**
- macOS 12.0+ (Monterey or newer)
- Apple Silicon Mac (M1/M2/M3)
- 6GB free RAM
- 8GB free disk space

**Recommended:**
- macOS 13.0+ (Ventura or newer)
- M2 or M3 with 16GB+ RAM
- 15GB+ free disk space
- Active cooling (avoid MacBook Air for heavy usage)

### Q: How much does it cost?

**A:** The LeoLM text correction feature is **completely free** for personal use. The model itself (LeoLM) is open source under MIT license. You only need:
- The Whisper Tool (free for personal use, commercial license available)
- LM Studio (free)
- The LeoLM model (free download)

No subscription fees, API costs, or hidden charges!

### Q: How long does the first setup take?

**A:**
- **Model download**: 15-30 minutes (7.5GB file)
- **Dependencies installation**: 5-10 minutes
- **Configuration**: 2-3 minutes
- **First model loading**: 30-60 seconds

**Total setup time: ~30-45 minutes** (mostly download time)

---

## 🔧 Installation and Configuration

### Q: Where should I download LeoLM from?

**A:** **Use LM Studio (recommended):**
1. Download LM Studio from https://lmstudio.ai/
2. Search for: `LeoLM-hesseianai-13b-chat`
3. Select: `mradermacher/LeoLM-hesseianai-13b-chat-GGUF`
4. Download: **Q4_K_M** variant (7.5GB)

**Alternative:** Direct download from Hugging Face, but LM Studio is easier and handles paths automatically.

### Q: Which model variant should I choose?

**A:** **Recommended: Q4_K_M**

| Variant | Size | Quality | Speed | RAM Need | Best for |
|---------|------|---------|--------|----------|----------|
| **Q4_K_M** | 7.5GB | Excellent | Fast | 6GB | **Most users** |
| Q3_K_M | 5.8GB | Good | Very Fast | 5GB | Low-end hardware |
| Q5_K_M | 9.1GB | Best | Slower | 8GB | Quality-focused |
| Q8_0 | 13.8GB | Perfect | Slowest | 12GB | Professional use |

**Q4_K_M offers the best balance of quality, speed, and resource usage.**

### Q: Can I use other language models?

**A:** Currently, the system is optimized specifically for LeoLM. Other models might work but are not tested or supported. LeoLM's German-specific training makes it significantly better for German text correction than general models like Llama or GPT variants.

### Q: My configuration file is missing. What do I do?

**A:** Create a minimal configuration:

```bash
# Create basic configuration
cat > ~/.whisper_tool.json << 'EOF'
{
  "text_correction": {
    "enabled": true,
    "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",
    "context_length": 2048,
    "correction_level": "standard",
    "temperature": 0.3
  }
}
EOF

# Verify the file was created
cat ~/.whisper_tool.json
```

---

## 🎯 Usage Questions

### Q: What are the different correction levels?

**A:**
- **Basic**: Fixes spelling, grammar, and punctuation. Best for casual use.
- **Advanced**: Includes style improvements and better readability. Good for professional documents.
- **Formal**: Professional language with formal tone. Ideal for business communication.

**Example:**
```
Original:  "das ist ein test mit viele fehler und schlecht grammar."

Basic:     "Das ist ein Test mit vielen Fehlern und schlechter Grammatik."
Advanced:  "Das ist ein Test mit mehreren Fehlern und mangelhafter Grammatik."
Formal:    "Dies ist eine Prüfung mit verschiedenen Fehlern und unzureichender Grammatik."
```

### Q: How do I correct text without transcribing?

**A:** **Option 1: Web Interface**
1. Start server: `./start_server.sh`
2. Go to: http://localhost:8090
3. Navigate to "Models" page
4. Find "Text Correction" section
5. Paste text and select correction level

**Option 2: Command Line**
```bash
# Direct text correction
whisper-tool correct "Dein text mit fehlern."

# From file
whisper-tool correct --input input.txt --output corrected.txt
```

**Option 3: Python API**
```python
from whisper_transcription_tool.module5_text_correction import LLMCorrector

with LLMCorrector() as corrector:
    result = corrector.correct_text("Dein text hier.")
    print(result)
```

### Q: Can I correct English text?

**A:** LeoLM is optimized for German text. While it may handle some English, the quality won't be as good. For best results:
- Use LeoLM for German text
- Consider other solutions for English text
- The tool can detect when text is primarily English and will warn you

### Q: How do I preserve the original formatting?

**A:** Add these settings to your configuration:

```json
{
  "text_correction": {
    "preserve_formatting": true,
    "preserve_line_breaks": true,
    "minimal_changes": true
  }
}
```

You can also use the "basic" correction level which makes fewer changes to structure.

---

## ⚡ Performance Questions

### Q: Why is text correction slow?

**A:** Several factors affect speed:

**Common causes:**
1. **First run**: Model loading takes 30-60 seconds initially
2. **Large context**: Reduce `context_length` from 4096 to 1024
3. **CPU mode**: Ensure `n_gpu_layers: -1` for GPU acceleration
4. **Memory pressure**: Close other applications
5. **Thermal throttling**: Mac is overheating

**Speed optimization:**
```json
{
  "text_correction": {
    "context_length": 1024,
    "correction_level": "basic",
    "temperature": 0.1,
    "max_tokens": 256,
    "batch_size": 1
  }
}
```

**Expected speeds:**
- M1: 20-40 chars/second
- M2: 40-70 chars/second
- M3: 60-100+ chars/second

### Q: How can I reduce memory usage?

**A:** **Low-memory configuration:**

```json
{
  "text_correction": {
    "n_gpu_layers": 15,        // Not all layers on GPU
    "context_length": 1024,    // Smaller context
    "use_mlock": false,        // Don't lock in RAM
    "batch_size": 1,           // Process sequentially
    "max_chunk_size": 400      // Smaller chunks
  }
}
```

**Additional steps:**
- Close Chrome, Photoshop, and other memory-intensive apps
- Restart your Mac to clear memory
- Monitor memory usage: Activity Monitor → Memory tab

### Q: Can I run this on a MacBook Air?

**A:** **Yes, but with limitations:**

**MacBook Air M1 (8GB RAM):**
- ✅ Works with careful configuration
- ⚠️  May be slow due to thermal throttling
- ⚠️  Requires closing other apps
- 📝 Use low-memory configuration

**MacBook Air M2/M3 (8GB RAM):**
- ✅ Better performance than M1
- ✅ Less thermal throttling
- 📝 Still recommend 16GB model for comfort

**Recommended Air settings:**
```json
{
  "text_correction": {
    "n_gpu_layers": 20,
    "context_length": 1024,
    "correction_level": "basic",
    "batch_size": 1
  }
}
```

---

## 🛠️ Troubleshooting Questions

### Q: I get "Model not found" error. What do I do?

**A:** **Step-by-step fix:**

1. **Find your model:**
   ```bash
   find ~ -name "*LeoLM*" -type f 2>/dev/null
   ```

2. **Common locations:**
   - `~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/`
   - `~/.cache/lm-studio/models/`
   - `~/Library/Caches/LMStudio/models/`

3. **Update configuration with correct path:**
   ```bash
   nano ~/.whisper_tool.json
   # Update model_path with the correct path
   ```

4. **If model doesn't exist:**
   - Open LM Studio
   - Download LeoLM model as described above

### Q: The correction produces weird results or hallucinations

**A:** **This usually means the temperature is too high or the prompt is confusing the model.**

**Quick fix:**
```json
{
  "text_correction": {
    "temperature": 0.1,      // Very low for factual corrections
    "correction_level": "basic",  // Less aggressive
    "max_tokens": 256        // Shorter responses
  }
}
```

**For professional documents:**
- Always review corrections manually
- Use "basic" level for factual content
- Consider processing smaller chunks
- Keep original text as backup

### Q: My Mac gets very hot during correction

**A:** **This is normal for intensive AI processing, but you can reduce the heat:**

**Immediate solutions:**
1. **Reduce GPU usage:**
   ```json
   {"n_gpu_layers": 10}  // Instead of -1
   ```

2. **Use CPU mode:**
   ```json
   {"n_gpu_layers": 0}   // CPU only, cooler but slower
   ```

3. **Take breaks:**
   - Process texts in smaller batches
   - Let Mac cool down between sessions

**Long-term solutions:**
- Use external cooling pad
- Improve room ventilation
- Consider Mac with better cooling (Pro/Max models)

### Q: Can I interrupt a long correction process?

**A:** **Yes:**

**Web interface:** Click the stop button or close the browser tab

**Command line:** Press `Ctrl+C`

**Python script:** Use KeyboardInterrupt handling:
```python
try:
    with LLMCorrector() as corrector:
        result = corrector.correct_text(long_text)
except KeyboardInterrupt:
    print("Correction interrupted by user")
```

The model will automatically clean up and free memory.

---

## 💡 Best Practices Questions

### Q: What's the best workflow for transcription + correction?

**A:** **Recommended workflow:**

1. **Transcribe first:**
   - Use Whisper for basic transcription
   - Review for obvious errors manually

2. **Then correct:**
   - Use LeoLM for text correction
   - Start with "basic" level
   - Upgrade to "advanced" if needed

3. **Always review:**
   - Check corrected text manually
   - Verify names, numbers, and facts
   - Save both original and corrected versions

**Web interface workflow:**
```
Upload Audio → Transcribe → Review → Enable Text Correction → Correct → Final Review
```

### Q: Should I use automatic correction during transcription?

**A:** **Depends on your use case:**

**Automatic correction (checkbox in web interface):**
- ✅ **Good for:** Casual use, quick drafts
- ⚠️  **Be careful with:** Important documents, names, technical terms

**Manual correction afterward:**
- ✅ **Good for:** Professional documents, important content
- ✅ **Allows:** Review of transcription quality first
- ✅ **Enables:** Selective correction

**Recommendation:** Start with manual correction until you trust the results, then consider automatic for routine content.

### Q: How do I handle technical terms and proper names?

**A:** **Proper names and technical terms can be challenging:**

**Prevention strategies:**
1. **Review transcription first** and manually fix obvious name/term errors
2. **Use "basic" correction level** which is more conservative
3. **Process smaller chunks** to maintain context
4. **Create a glossary** of important terms to check afterward

**Example workflow for medical/technical content:**
```python
# Pre-process to protect terms
def protect_terms(text, terms_list):
    for term in terms_list:
        text = text.replace(term, f"[PROTECTED_{term}_PROTECTED]")
    return text

# Restore after correction
def restore_terms(text, terms_list):
    for term in terms_list:
        text = text.replace(f"[PROTECTED_{term}_PROTECTED]", term)
    return text
```

### Q: What file formats are supported?

**A:** **Input formats:**
- ✅ Plain text (.txt)
- ✅ Transcription formats (.srt, .vtt with text extraction)
- ✅ Direct text input (web interface, command line)

**Output formats:**
- ✅ Plain text (.txt)
- ✅ Same format as input
- ✅ Side-by-side comparison (planned feature)

**Note:** The tool focuses on text content and preserves basic formatting, but complex document structures (Word, PDF) need external conversion.

---

## 🎛️ Advanced Usage Questions

### Q: Can I customize the correction prompts?

**A:** **Not directly in the current version**, but you can modify the correction behavior through configuration:

```json
{
  "text_correction": {
    "correction_level": "basic",    // Conservative corrections
    "temperature": 0.1,             // Very consistent
    "preserve_style": true,         // Keep original style
    "minimal_changes": true         // Reduce modifications
  }
}
```

**Future versions** will support custom prompts. For now, the three built-in levels (basic/advanced/formal) cover most use cases.

### Q: How do I batch process multiple files?

**A:** **Command line batch processing:**

```bash
# Process all .txt files in a directory
for file in input_directory/*.txt; do
    whisper-tool correct --input "$file" --output "corrected_$(basename "$file")"
done
```

**Python script for batch processing:**
```python
import os
from pathlib import Path
from whisper_transcription_tool.module5_text_correction import LLMCorrector

def batch_correct_directory(input_dir, output_dir):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    with LLMCorrector() as corrector:
        for txt_file in input_path.glob("*.txt"):
            with open(txt_file) as f:
                text = f.read()

            corrected = corrector.correct_text(text)

            output_file = output_path / f"corrected_{txt_file.name}"
            with open(output_file, 'w') as f:
                f.write(corrected)

            print(f"✅ Processed: {txt_file.name}")

# Usage
batch_correct_directory("./input_texts", "./corrected_texts")
```

### Q: Can I run this on a server or in the cloud?

**A:** **Technical considerations:**

**Possible but not recommended because:**
- ❌ Designed for Apple Silicon (Metal GPU)
- ❌ Model size makes cloud deployment expensive
- ❌ Current version assumes macOS environment

**If you want server deployment:**
- 🔧 Would need significant modifications
- 🔧 Different GPU acceleration (CUDA instead of Metal)
- 🔧 Different dependency management
- 💰 Commercial license required

**Better alternatives:**
- Use the Mac app remotely (screen sharing)
- Process files locally and sync results
- Contact us for enterprise solutions: mail@goaiex.com

---

## 🔒 Privacy and Security Questions

### Q: Is my data sent to the internet?

**A:** **No! Everything runs locally:**
- ✅ **Model runs on your Mac** - no data sent to external servers
- ✅ **No API calls** to OpenAI, Google, or other cloud services
- ✅ **No telemetry** or usage tracking
- ✅ **Offline capable** - works without internet connection

**The only internet usage is:**
- Model download (one-time setup)
- Software updates (optional)
- License validation (for commercial use)

### Q: What happens to my transcriptions?

**A:** **Your data stays on your Mac:**
- 📁 **Transcriptions saved locally** in the `transcriptions/` folder
- 🗑️ **Temp files cleaned up** automatically
- 💾 **You control all data** - delete, move, backup as needed
- 🔐 **No cloud storage** unless you choose to use it

### Q: Are there any privacy risks?

**A:** **Minimal risks with standard precautions:**

**Low risks:**
- ✅ Local processing means no data leaves your device
- ✅ Open source model (LeoLM) with transparent training
- ✅ No user accounts or cloud dependencies

**Standard precautions:**
- 🔐 Keep your Mac secure with FileVault encryption
- 🔐 Use secure networks when downloading models
- 🔐 Regular backups of important transcriptions

**Note:** For highly sensitive content (medical, legal, confidential), always verify your organization's AI usage policies.

---

## 💰 Commercial and Licensing Questions

### Q: Can I use this for my business?

**A:** **Yes, with proper licensing:**

**Personal use:** Free
**Commercial use:** Requires license

**To get a commercial license:**
- 📧 Email: mail@goaiex.com
- 🌐 Website: www.goaiex.com
- 💬 Describe your use case and company size

**LeoLM model:** MIT license allows commercial use

### Q: What counts as commercial use?

**A:** **Commercial use includes:**
- ✅ Using in a business environment
- ✅ Processing client/customer content
- ✅ Revenue-generating activities
- ✅ Professional services

**Personal use includes:**
- ✅ Personal projects and learning
- ✅ Academic research
- ✅ Non-profit personal use

**When in doubt:** Contact us for clarification - we're reasonable!

### Q: How much does a commercial license cost?

**A:** **Flexible pricing based on:**
- Company size
- Usage volume
- Support requirements
- Additional features needed

**Contact us for a quote:** mail@goaiex.com

We offer reasonable pricing for small businesses and startups.

---

## 🔮 Future Features Questions

### Q: What features are planned?

**A:** **Upcoming features:**
- 🌍 **Multi-language support** (English, French, Spanish)
- 📝 **Custom prompts** and correction styles
- 📊 **Quality metrics** and comparison tools
- 🔄 **Real-time correction** during transcription
- 📱 **Mobile companion app**
- 🧠 **Fine-tuning** for specific domains

### Q: Will you support other models?

**A:** **Potentially, but LeoLM remains primary:**
- LeoLM provides excellent German performance
- Other models would need extensive testing
- Community requests will influence priorities

**If you need specific model support:** Let us know your use case!

### Q: Can I contribute to the project?

**A:** **Yes! Contributions are welcome:**

**Ways to contribute:**
- 🐛 **Bug reports** via GitHub Issues
- 💡 **Feature suggestions** and feedback
- 📝 **Documentation** improvements
- 🧪 **Testing** on different hardware
- 💰 **Sponsorship** for continued development

**GitHub:** https://github.com/cubetribe/WhisperCC_MacOS_Local

---

## ❓ Still Have Questions?

### Getting More Help

**📚 Documentation:**
- [Complete User Guide](TEXTKORREKTUR.md)
- [Configuration Examples](CONFIG_EXAMPLES.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

**🆘 Support Channels:**
- GitHub Issues (bugs and feature requests)
- Email: mail@goaiex.com (commercial support)
- Community discussions (planned)

**📞 Before Contacting Support:**
1. Check this FAQ
2. Review troubleshooting guide
3. Run diagnostic script
4. Search GitHub issues

**💡 Quick Questions:**
Post as GitHub discussions for community help!

---

**Version**: 1.0.0 | **Date**: September 2025
**Created by**: DocsNarrator Agent | **Website**: [www.goaiex.com](https://www.goaiex.com)

This FAQ is regularly updated based on community questions. Don't see your question? Ask us!