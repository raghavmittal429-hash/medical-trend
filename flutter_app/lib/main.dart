import 'dart:convert';
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter/foundation.dart';
import 'theme/medisimple_theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:http/http.dart' as http;
import 'package:file_picker/file_picker.dart';
import 'package:fl_chart/fl_chart.dart';
import 'dart:async';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

void main() {
  runApp(const MedicalCDSSApp());
}

class MedicalCDSSApp extends StatelessWidget {
  const MedicalCDSSApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MediSimple',
      debugShowCheckedModeBanner: false,
      theme: MediSimpleTheme.light,
      home: const HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _currentIndex = 0;
  final FlutterTts _tts = FlutterTts();

  // Data state
  Map<String, dynamic>? _reportData;
  bool _isLoading = false;
  bool _isTranslating = false;
  bool _isDownloadingPdf = false;
  String _selectedLanguage = 'English';
  bool _ttsEnabled = true;
  String? _selectedVoiceName;
  List<dynamic> _availableVoices = [];
  List<html.SpeechSynthesisVoice> _speechVoices = [];
  String? _currentJobId;
  Timer? _pollingTimer;

  final List<Map<String, String>> _languages = [
    {'code': 'en', 'name': 'English', 'native': 'English'},
    {'code': 'hi', 'name': 'Hindi', 'native': 'हिन्दी'},
    {'code': 'bn', 'name': 'Bengali', 'native': 'বাংলা'},
    {'code': 'ta', 'name': 'Tamil', 'native': 'தமிழ்'},
    {'code': 'te', 'name': 'Telugu', 'native': 'తెలుగు'},
    {'code': 'mr', 'name': 'Marathi', 'native': 'मराठी'},
    {'code': 'gu', 'name': 'Gujarati', 'native': 'ગુજરાતી'},
    {'code': 'kn', 'name': 'Kannada', 'native': 'ಕನ್ನಡ'},
    {'code': 'ml', 'name': 'Malayalam', 'native': 'മലയാളം'},
  ];

  @override
  void initState() {
    super.initState();
    _initTts();
  }

  Future<void> _initTts() async {
    await _tts.setSpeechRate(0.45);
    await _tts.setPitch(1.0);
    await _tts.awaitSpeakCompletion(true);
    if (kIsWeb) {
      await _loadWebVoices();
    }
    await _loadAvailableVoices();
    await _applyVoiceForLanguage(_selectedLanguage);
  }

  Future<void> _loadWebVoices() async {
    try {
      _speechVoices = List<html.SpeechSynthesisVoice>.from(html.window.speechSynthesis.getVoices());
      if (_speechVoices.isEmpty) {
        html.window.speechSynthesis.onVoicesChanged.listen((_) {
          final voices = html.window.speechSynthesis.getVoices();
          _speechVoices = List<html.SpeechSynthesisVoice>.from(voices);
          setState(() {});
        });
      }
    } catch (_) {
      _speechVoices = [];
    }
  }

  Future<void> _loadAvailableVoices() async {
    try {
      final voices = await _tts.getVoices;
      if (voices is List) {
        _availableVoices = voices;
      }
    } catch (_) {
      _availableVoices = [];
    }
  }

  Future<void> _applyVoiceForLanguage(String language) async {
    final targetLocale = _ttsLocaleFor(language);
    dynamic bestVoice;

    if (_availableVoices.isNotEmpty) {
      final localeMatches = _availableVoices.where((voice) {
        final voiceLocale = _voiceLocaleOf(voice).toLowerCase();
        return voiceLocale.contains(targetLocale.toLowerCase()) || targetLocale.toLowerCase().contains(voiceLocale);
      }).toList();

      if (localeMatches.isNotEmpty) {
        bestVoice = _preferredVoice(localeMatches);
      } else {
        bestVoice = _preferredVoice(_availableVoices);
      }
    }

    if (bestVoice != null) {
      _selectedVoiceName = _voiceNameOf(bestVoice);
      await _setTtsVoice(bestVoice);
    }

    await _tts.setLanguage(targetLocale);
    await _tts.setSpeechRate(0.45);
    await _tts.setPitch(1.0);
  }

  String _voiceLocaleOf(dynamic voice) {
    if (voice is Map) {
      final locale = voice['locale'] ?? voice['language'] ?? voice['name'];
      return locale?.toString() ?? '';
    }
    return voice.toString();
  }

  String _voiceNameOf(dynamic voice) {
    if (voice is Map) {
      return voice['name']?.toString() ?? _voiceLocaleOf(voice);
    }
    return voice.toString();
  }

  dynamic _preferredVoice(List<dynamic> voices) {
    final preferred = voices.firstWhere(
      (voice) {
        final name = _voiceNameOf(voice).toLowerCase();
        return name.contains('soft') || name.contains('smooth') || name.contains('female') || name.contains('male');
      },
      orElse: () => voices.first,
    );
    return preferred;
  }

  Future<void> _setTtsVoice(dynamic voice) async {
    try {
      if (voice is Map) {
        final settings = <String, String>{};
        if (voice.containsKey('name')) settings['name'] = voice['name'].toString();
        if (voice.containsKey('locale')) settings['locale'] = voice['locale'].toString();
        if (settings.isNotEmpty) {
          await _tts.setVoice(settings);
        }
      }
    } catch (_) {
      // Ignore voice selection failure; fallback to language-only mode.
    }
  }

  html.SpeechSynthesisVoice? _chooseWebVoice(String locale) {
    if (_speechVoices.isEmpty) return null;
    final languageCode = locale.split('-').first.toLowerCase();
    final exact = _speechVoices.where((voice) {
      return voice.lang?.toLowerCase().contains(locale.toLowerCase()) ?? false;
    }).toList();
    if (exact.isNotEmpty) return exact.first;

    final partial = _speechVoices.where((voice) {
      return voice.lang?.toLowerCase().startsWith(languageCode) ?? false;
    }).toList();
    if (partial.isNotEmpty) return partial.first;

    return _speechVoices.first;
  }

  Future<void> _speakWeb(String text) async {
    if (text.isEmpty || !_ttsEnabled) return;
    try {
      final locale = _ttsLocaleFor(_selectedLanguage);
      final utterance = html.SpeechSynthesisUtterance(text)
        ..lang = locale
        ..rate = 0.9
        ..pitch = 1.0
        ..volume = 1.0;

      final voice = _chooseWebVoice(locale);
      if (voice != null) {
        utterance.voice = voice;
      }

      html.window.speechSynthesis.cancel();
      html.window.speechSynthesis.speak(utterance);
    } catch (_) {
      // fallback: nothing to do, maybe flutter_tts will still work
    }
  }

  Future<void> _setTtsLanguage(String locale) async {
    try {
      await _tts.setLanguage(locale);
    } catch (_) {
      if (locale != 'en-US') {
        await _tts.setLanguage('en-US');
      }
    }
  }

  // Base URL is injected at build time via --dart-define=API_BASE_URL=https://your-app.up.railway.app
  // Falls back to localhost for local development
  static const String _baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://medical-trend-11.onrender.com',
  );

  Uri _buildApiUrl(String path) {
    return Uri.parse('$_baseUrl$path');
  }

  Future<void> _pickFile() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf'],
        allowMultiple: false,
        withData: true,
      );

      if (result != null && result.files.isNotEmpty) {
        final file = result.files.first;
        if (file.bytes != null) {
          await _processFileBytes(file.bytes!, file.name);
        } else {
          _showError('Unable to read file data. Please try again.');
        }
      }
    } catch (e) {
      _showError('Error picking file: $e');
    }
  }

  Future<void> _processFileBytes(Uint8List bytes, String fileName) async {
    setState(() {
      _isLoading = true;
      _reportData = null;
    });

    final apiUrl = _buildApiUrl('/upload');

    try {
      final request = http.MultipartRequest('POST', apiUrl);
      request.files.add(http.MultipartFile.fromBytes(
        'file',
        bytes,
        filename: fileName,
      ));
      request.fields['language'] = _selectedLanguage;

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final responseData = json.decode(response.body);
        final jobId = responseData['job_id'];

        if (jobId != null) {
          _startJobPolling(jobId);
        } else {
          setState(() {
            _reportData = responseData;
            _isLoading = false;
          });
        }
      } else {
        _showError('Upload failed: ${response.statusCode}');
      }
    } catch (e) {
      _showError('Connection error: $e\nMake sure backend is running');
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  void _startJobPolling(String jobId) {
    if (_currentJobId != null) {
      _pollingTimer?.cancel();
    }
    _currentJobId = jobId;

    // Poll every 2 seconds for job status
    _pollingTimer = Timer.periodic(const Duration(seconds: 2), (timer) async {
      try {
        final statusUrl = _buildApiUrl('/job/$jobId');
        final response = await http.get(statusUrl);

        if (response.statusCode == 200) {
          final statusData = json.decode(response.body);

          if (statusData['status'] == 'completed') {
            setState(() {
              _reportData = statusData['result'];
              _isLoading = false;
            });
            _pollingTimer?.cancel();
            _currentJobId = null;
          } else if (statusData['status'] == 'failed') {
            _showError('Processing failed: ${statusData['error']}');
            setState(() { _isLoading = false; });
            _pollingTimer?.cancel();
            _currentJobId = null;
          }
        } else {
          _showError('Error checking job status');
          setState(() { _isLoading = false; });
          _pollingTimer?.cancel();
          _currentJobId = null;
        }
      } catch (e) {
        _showError('Connection error while checking status: $e');
        setState(() { _isLoading = false; });
        _pollingTimer?.cancel();
        _currentJobId = null;
      }
    });
  
  }

  Future<void> _speak(String text) async {
    if (text.isEmpty || !_ttsEnabled) return;

    if (kIsWeb) {
      await _speakWeb(text);
      return;
    }

    await _tts.stop();
    await _applyVoiceForLanguage(_selectedLanguage);
    await _tts.speak(text);
  }

  String _ttsLocaleFor(String language) {
    const locales = {
      'English': 'en-US',
      'Hindi': 'hi-IN',
      'Bengali': 'bn-IN',
      'Tamil': 'ta-IN',
      'Telugu': 'te-IN',
      'Marathi': 'mr-IN',
      'Gujarati': 'gu-IN',
      'Kannada': 'kn-IN',
      'Malayalam': 'ml-IN',
    };
    return locales[language] ?? 'en-US';
  }

  void _showFilePicker() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => Container(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.picture_as_pdf),
              title: const Text('Choose PDF'),
              subtitle: const Text('Upload PDF medical report'),
              onTap: () {
                Navigator.pop(context);
                _pickFile();
              },
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Future<void> _downloadPdf() async {
    if (_reportData == null) return;
    setState(() => _isDownloadingPdf = true);
    try {
      final pdf = pw.Document();
      final data = _reportData!;
      final risk = ((data['risk_probability'] ?? 0) as num).toDouble();
      final riskPct = '${(risk * 100).toStringAsFixed(1)}%';
      final lang = _selectedLanguage;
      final isEnglish = lang == 'English';

      // Pick the right Noto font based on the selected language script
      String fontAssetRegular = 'assets/fonts/NotoSans-Regular.ttf';
      String fontAssetBold    = 'assets/fonts/NotoSans-Bold.ttf';
      if (['Hindi', 'Marathi', 'Nepali'].contains(lang)) {
        fontAssetRegular = 'assets/fonts/NotoSansDevanagari-Regular.ttf';
        fontAssetBold    = 'assets/fonts/NotoSansDevanagari-Bold.ttf';
      } else if (lang == 'Tamil') {
        fontAssetRegular = 'assets/fonts/NotoSansTamil-Regular.ttf';
        fontAssetBold    = 'assets/fonts/NotoSansTamil-Regular.ttf';
      } else if (['Bengali', 'Assamese'].contains(lang)) {
        fontAssetRegular = 'assets/fonts/NotoSansBengali-Regular.ttf';
        fontAssetBold    = 'assets/fonts/NotoSansBengali-Regular.ttf';
      } else if (['Arabic', 'Urdu', 'Persian'].contains(lang)) {
        fontAssetRegular = 'assets/fonts/NotoSansArabic-Regular.ttf';
        fontAssetBold    = 'assets/fonts/NotoSansArabic-Regular.ttf';
      }

      final fontDataRegular = await rootBundle.load(fontAssetRegular);
      final fontDataBold    = await rootBundle.load(fontAssetBold);
      final ttfRegular = pw.Font.ttf(fontDataRegular);
      final ttfBold    = pw.Font.ttf(fontDataBold);

      // Also load NotoSans as fallback for Latin characters in mixed content
      final fontDataFallback = await rootBundle.load('assets/fonts/NotoSans-Regular.ttf');
      final ttfFallback = pw.Font.ttf(fontDataFallback);

      final suggestions = (data['suggestions'] as List? ?? []).map((s) => s.toString()).toList();
      final translatedSuggestions = (data['translated_suggestions'] as List? ?? []).map((s) => s.toString()).toList();
      final translatedExplanation = (data['translated_explanation'] ?? '').toString();
      final diseaseEn    = (data['disease_explanation_en'] ?? '').toString();
      final solutionEn   = (data['solution_plan_en'] ?? '').toString();
      final diseaseLang  = (data['disease_explanation_lang'] ?? data['disease_explanation_hi'] ?? '').toString();
      final solutionLang = (data['solution_plan_lang'] ?? data['solution_plan_hi'] ?? '').toString();
      final medicalSummary    = (data['medical_summary'] ?? '').toString();
      final simpleExplanation = (data['simple_explanation'] ?? '').toString();

      // Each pw.Text must fit in one page — split long body into sentences so
      // MultiPage can break between them. Never wrap text in Container/Padding/Column.
      final List<pw.Widget> items = [];
      final _bodyStyle  = pw.TextStyle(font: ttfRegular, fontFallback: [ttfFallback], fontSize: 10, lineSpacing: 5);
      final _titleStyle = pw.TextStyle(font: ttfBold, fontFallback: [ttfFallback], fontSize: 12, fontWeight: pw.FontWeight.bold, color: PdfColors.red900);
      final _headerStyle = pw.TextStyle(font: ttfBold, fontFallback: [ttfFallback], fontSize: 16, fontWeight: pw.FontWeight.bold, color: PdfColors.red900);
      final _subHeaderStyle = pw.TextStyle(font: ttfRegular, fontFallback: [ttfFallback], fontSize: 9, color: PdfColors.grey600);
      final _riskStyle = pw.TextStyle(font: ttfBold, fontFallback: [ttfFallback], fontSize: 10, fontWeight: pw.FontWeight.bold,
          color: risk > 0.6 ? PdfColors.red800 : risk > 0.3 ? PdfColors.orange800 : PdfColors.green800);
      final _footerStyle = pw.TextStyle(font: ttfRegular, fontFallback: [ttfFallback], fontSize: 8, color: PdfColors.grey500);

      // Split on sentence endings or newlines so each chunk is small
      List<String> _splitBody(String body) {
        final raw = body.replaceAll('\r\n', '\n').replaceAll('\r', '\n');
        final List<String> parts = [];
        for (final para in raw.split('\n')) {
          final p = para.trim();
          if (p.isEmpty) continue;
          // Further split long paragraphs on '. ' boundaries (~150 chars max each)
          if (p.length <= 150) {
            parts.add(p);
          } else {
            final sentences = p.split(RegExp(r'(?<=[.!?])\s+'));
            for (final s in sentences) {
              final t = s.trim();
              if (t.isNotEmpty) parts.add(t);
            }
          }
        }
        return parts.isEmpty ? [body.trim()] : parts;
      }

      void addSection(String title, String body) {
        if (body.trim().isEmpty) return;
        items.add(pw.SizedBox(height: 10));
        items.add(pw.Text(title, style: _titleStyle));
        items.add(pw.SizedBox(height: 3));
        for (final chunk in _splitBody(body)) {
          items.add(pw.Text(chunk, style: _bodyStyle));
          items.add(pw.SizedBox(height: 2));
        }
        items.add(pw.SizedBox(height: 2));
        items.add(pw.Divider(color: PdfColors.grey300, thickness: 0.5));
      }

      void addBullets(String title, List<String> bullets) {
        if (bullets.isEmpty) return;
        items.add(pw.SizedBox(height: 10));
        items.add(pw.Text(title, style: _titleStyle));
        items.add(pw.SizedBox(height: 3));
        for (final b in bullets) {
          // Each bullet may itself be long — split it too
          final chunks = _splitBody(b);
          items.add(pw.Text('  \u2022  ${chunks.first}', style: _bodyStyle));
          for (final extra in chunks.skip(1)) {
            items.add(pw.Text('     $extra', style: _bodyStyle));
          }
          items.add(pw.SizedBox(height: 2));
        }
        items.add(pw.SizedBox(height: 2));
        items.add(pw.Divider(color: PdfColors.grey300, thickness: 0.5));
      }

      addSection('Medical Summary', medicalSummary);
      addSection('Simple Explanation', simpleExplanation);
      if (!isEnglish && translatedExplanation.isNotEmpty)
        addSection('$lang Explanation', translatedExplanation);
      addSection('Disease Explanation', diseaseEn);
      addSection('Solutions to Improve', solutionEn);
      if (!isEnglish && diseaseLang.isNotEmpty)
        addSection('Disease Explanation ($lang)', diseaseLang);
      if (!isEnglish && solutionLang.isNotEmpty)
        addSection('Solutions ($lang)', solutionLang);
      addBullets('AI Suggestions', suggestions);
      if (!isEnglish && translatedSuggestions.isNotEmpty)
        addBullets('$lang Suggestions', translatedSuggestions);

      pdf.addPage(
        pw.MultiPage(
          pageFormat: PdfPageFormat.a4,
          margin: const pw.EdgeInsets.symmetric(horizontal: 36, vertical: 32),
          maxPages: 100,
          header: (ctx) => pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Row(
                mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                children: [
                  pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
                    pw.Text('Medical Report Summary', style: _headerStyle),
                    pw.Text('Generated by MediSimple  \u2022  ${data['report_date'] ?? ""}', style: _subHeaderStyle),
                  ]),
                  pw.Text('Risk: $riskPct', style: _riskStyle),
                ],
              ),
              pw.Divider(color: PdfColors.red300, thickness: 1),
              pw.SizedBox(height: 2),
            ],
          ),
          footer: (ctx) => pw.Row(
            mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
            children: [
              pw.Text('MediSimple \u2014 Confidential', style: _footerStyle),
              pw.Text('Page ${ctx.pageNumber} of ${ctx.pagesCount}', style: _footerStyle),
            ],
          ),
          build: (ctx) => items,
        ),
      );
      final bytes = await pdf.save();
      // ignore: avoid_web_libraries_in_flutter
      final blob = html.Blob([bytes], 'application/pdf');
      final url = html.Url.createObjectUrlFromBlob(blob);
      final anchor = html.AnchorElement(href: url)
        ..setAttribute('download', 'medical_report_${DateTime.now().millisecondsSinceEpoch}.pdf')
        ..click();
      html.Url.revokeObjectUrl(url);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('✓ PDF downloaded successfully'),
          backgroundColor: Color(0xFF1565C0),
          behavior: SnackBarBehavior.floating,
          duration: Duration(seconds: 2),
        ));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Failed to generate PDF: $e'),
          backgroundColor: Colors.red.shade700,
          behavior: SnackBarBehavior.floating,
        ));
      }
    } finally {
      if (mounted) setState(() => _isDownloadingPdf = false);
    }
  }

  Future<void> _retranslate(String langName) async {
    if (_reportData == null) return;
    setState(() => _isTranslating = true);

    try {
      final url  = _buildApiUrl('/retranslate');
      final body = json.encode({
        'parsed_data':            _reportData!['parsed_data'] ?? '',
        'language':               langName,
        'suggestions':            _reportData!['suggestions'] ?? [],
        'medical_summary':        _reportData!['medical_summary'] ?? '',
        'simplified_explanation': _reportData!['simple_explanation'] ?? '',
        'temporal_analysis':      _reportData!['temporal_analysis'] ?? '',
        'causal_analysis':        _reportData!['causal_analysis'] ?? '',
        'risk_probability':       _reportData!['risk_probability'] ?? 0.0,
        'patient_id':             _reportData!['patient_id'],
        'report_date':            _reportData!['report_date'] ?? '',
        'disease_explanation_en': _reportData!['disease_explanation_en'] ?? '',
        'solution_plan_en':       _reportData!['solution_plan_en'] ?? '',
      });

      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: body,
      ).timeout(
        const Duration(seconds: 120),
        onTimeout: () => throw Exception('Translation timed out. Please try again.'),
      );

      if (response.statusCode == 200) {
        final newData = json.decode(response.body);
        setState(() {
          _reportData = {
            ..._reportData!,
            'translated_explanation':   newData['translated_explanation'] ?? '',
            'translated_suggestions':   newData['translated_suggestions'] ?? [],
            'disease_explanation_lang': newData['disease_explanation_hi'] ?? newData['disease_explanation_lang'] ?? '',
            'solution_plan_lang':       newData['solution_plan_hi'] ?? newData['solution_plan_lang'] ?? '',
            'disease_explanation_hi':   newData['disease_explanation_hi'] ?? '',
            'solution_plan_hi':         newData['solution_plan_hi'] ?? '',
            'target_language':          langName,
          };
        });
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text('✓ Translated to $langName'),
            backgroundColor: const Color(0xFF2E7D32),
            behavior: SnackBarBehavior.floating,
            duration: const Duration(seconds: 2),
          ));
        }
      } else {
        _showError('Translation failed (${response.statusCode}). Please try again.');
        setState(() => _selectedLanguage = 'English');
      }
    } catch (e) {
      if (mounted) _showError('Translation error: $e');
      setState(() => _selectedLanguage = 'English');
    } finally {
      if (mounted) setState(() => _isTranslating = false);
    }
  }

  void _showTranslationErrorDialog(String message) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        title: const Row(
          children: [
            Icon(Icons.translate, color: Color(0xFFA01A1A)),
            SizedBox(width: 8),
            Text('Translation Unavailable'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(message, style: const TextStyle(fontSize: 14)),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFFFDF0F0),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xFFEDCCCC)),
              ),
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('To enable translation:',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  SizedBox(height: 6),
                  Text('1. Make sure the backend server is running',
                      style: TextStyle(fontSize: 12)),
                  Text('2. Set ANTHROPIC_API_KEY in your backend .env file',
                      style: TextStyle(fontSize: 12)),
                  Text('3. Run: uvicorn main:app --port 8000',
                      style: TextStyle(fontSize: 12)),
                ],
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('OK', style: TextStyle(color: Color(0xFFA01A1A))),
          ),
        ],
      ),
    );
  }

  void _showLanguageSelector() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setSheetState) => SafeArea(
            child: Padding(
              padding: EdgeInsets.fromLTRB(16, 20, 16, MediaQuery.of(context).viewInsets.bottom + 16),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Header
                  Row(
                    children: [
                      Container(
                        width: 36, height: 36,
                        decoration: BoxDecoration(
                          color: const Color(0xFFFDF0F0),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Icon(Icons.language, color: Color(0xFFA01A1A), size: 20),
                      ),
                      const SizedBox(width: 12),
                      const Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Select Language',
                            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
                          Text('Report will be retranslated automatically',
                            style: TextStyle(fontSize: 12, color: Colors.grey)),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  const Divider(height: 1),
                  const SizedBox(height: 4),
                  // Scrollable language list
                  ConstrainedBox(
                    constraints: BoxConstraints(
                      maxHeight: MediaQuery.of(context).size.height * 0.5,
                    ),
                    child: ListView(
                      shrinkWrap: true,
                      children: _languages.map((lang) {
                        final isSelected = _selectedLanguage == lang['name'];
                        return ListTile(
                          contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          leading: Container(
                            width: 40, height: 40,
                            decoration: BoxDecoration(
                              color: isSelected ? const Color(0xFFFDF0F0) : const Color(0xFFF5F5F5),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            alignment: Alignment.center,
                            child: Text(lang['native']![0],
                              style: TextStyle(
                                fontSize: 18,
                                color: isSelected ? const Color(0xFFA01A1A) : Colors.grey.shade600,
                                fontWeight: FontWeight.bold,
                              )),
                          ),
                          title: Text(lang['name']!,
                            style: TextStyle(
                              fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                              color: isSelected ? const Color(0xFFA01A1A) : null,
                            )),
                          subtitle: Text(lang['native']!,
                            style: const TextStyle(fontSize: 12)),
                          trailing: isSelected
                              ? const Icon(Icons.check_circle, color: Color(0xFFA01A1A), size: 22)
                              : null,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                          tileColor: isSelected ? const Color(0xFFFDF0F0) : null,
                          onTap: () {
                            final newLang = lang['name']!;
                            Navigator.pop(context);
                            if (newLang != _selectedLanguage) {
                              setState(() {
                                _selectedLanguage = newLang;
                                // Clear stale translated content so old language doesn't show
                                if (_reportData != null) {
                                  _reportData = {
                                    ..._reportData!,
                                    'translated_explanation':   '',
                                    'translated_suggestions':   [],
                                    'disease_explanation_lang': '',
                                    'solution_plan_lang':       '',
                                  };
                                }
                              });
                              _applyVoiceForLanguage(newLang);
                              if (_reportData != null) {
                                _retranslate(newLang);
                              }
                            }
                          },
                        );
                      }).toList(),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  void _showVoiceSelector() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return SafeArea(
          child: Padding(
            padding: EdgeInsets.fromLTRB(16, 20, 16, MediaQuery.of(context).viewInsets.bottom + 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      width: 36, height: 36,
                      decoration: BoxDecoration(
                        color: const Color(0xFFFDF0F0),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Icon(Icons.hearing, color: Color(0xFFA01A1A), size: 20),
                    ),
                    const SizedBox(width: 12),
                    const Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Select Voice Model',
                          style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
                        Text('Choose a smoother voice for playback',
                          style: TextStyle(fontSize: 12, color: Colors.grey)),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                const Divider(height: 1),
                const SizedBox(height: 4),
                if (_availableVoices.isEmpty)
                  const Padding(
                    padding: EdgeInsets.all(16),
                    child: Text('No available voices detected on this device.', style: TextStyle(fontSize: 14)),
                  )
                else
                  ConstrainedBox(
                    constraints: BoxConstraints(
                      maxHeight: MediaQuery.of(context).size.height * 0.55,
                    ),
                    child: ListView.builder(
                      shrinkWrap: true,
                      itemCount: _availableVoices.length,
                      itemBuilder: (context, index) {
                        final voice = _availableVoices[index];
                        final voiceName = _voiceNameOf(voice);
                        final voiceLocale = _voiceLocaleOf(voice);
                        final isSelected = _selectedVoiceName == voiceName;
                        return ListTile(
                          title: Text(voiceName),
                          subtitle: Text(voiceLocale),
                          trailing: isSelected ? const Icon(Icons.check_circle, color: Color(0xFFA01A1A)) : null,
                          onTap: () async {
                            Navigator.pop(context);
                            setState(() {
                              _selectedVoiceName = voiceName;
                            });
                            await _setTtsVoice(voice);
                            await _setTtsLanguage(_ttsLocaleFor(_selectedLanguage));
                          },
                        );
                      },
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      resizeToAvoidBottomInset: false,
      appBar: AppBar(
        title: Row(
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Image.asset(
                'assets/images/medisimple_logo.jpg',
                width: 44,
                height: 44,
                fit: BoxFit.cover,
              ),
            ),
            const SizedBox(width: 12),
            const Text(
              'MediSimple',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 20,
                color: Colors.white,
              ),
            ),
          ],
        ),
        backgroundColor: const Color(0xFFA01A1A),
        actions: [
          if (_isTranslating)
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 8),
              child: Center(
                child: SizedBox(
                  width: 18, height: 18,
                  child: CircularProgressIndicator(
                    strokeWidth: 2, color: Colors.white,
                  ),
                ),
              ),
            )
          else
            Padding(
              padding: const EdgeInsets.only(right: 4),
              child: TextButton.icon(
                onPressed: _showLanguageSelector,
                icon: const Icon(Icons.language, color: Colors.white, size: 18),
                label: Text(
                  _selectedLanguage,
                  style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600),
                ),
                style: TextButton.styleFrom(
                  backgroundColor: Colors.white.withValues(alpha: 0.15),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                ),
              ),
            ),
        ],
      ),
      body: Stack(
        children: [
          IndexedStack(
            index: _currentIndex,
            children: [
              _buildUploadTab(),
              _buildExplainTab(),
              _buildSuggestionsTab(),
              _buildTrendsTab(),
              _buildSettingsTab(),
            ],
          ),
          // Full-screen translating overlay — covers ALL tabs
          if (_isTranslating)
            Container(
              color: Colors.black.withValues(alpha: 0.45),
              child: Center(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 24),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.15),
                        blurRadius: 20, offset: const Offset(0, 8),
                      ),
                    ],
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const SizedBox(
                        width: 48, height: 48,
                        child: CircularProgressIndicator(
                          strokeWidth: 3,
                          color: Color(0xFFA01A1A),
                        ),
                      ),
                      const SizedBox(height: 20),
                      Text(
                        'Translating to $_selectedLanguage',
                        style: const TextStyle(
                          fontSize: 16, fontWeight: FontWeight.w700,
                          color: Color(0xFF2B2B2B),
                        ),
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        'Explanation, suggestions, disease\nand solution are being translated…',
                        style: TextStyle(fontSize: 13, color: Colors.grey),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) => setState(() => _currentIndex = index),
        backgroundColor: Colors.white,
        indicatorColor: Color(0xFFA01A1A).withValues(alpha: 0.2),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.upload_file, color: Colors.grey),
            selectedIcon: Icon(Icons.upload_file, color: Color(0xFFA01A1A)),
            label: 'Upload',
          ),
          NavigationDestination(
            icon: Icon(Icons.description_outlined, color: Colors.grey),
            selectedIcon: Icon(Icons.description, color: Color(0xFFA01A1A)),
            label: 'Explain',
          ),
          NavigationDestination(
            icon: Icon(Icons.tips_and_updates_outlined, color: Colors.grey),
            selectedIcon: Icon(Icons.tips_and_updates, color: Color(0xFFA01A1A)),
            label: 'Suggestions',
          ),
          NavigationDestination(
            icon: Icon(Icons.show_chart, color: Colors.grey),
            selectedIcon: Icon(Icons.show_chart, color: Color(0xFFA01A1A)),
            label: 'Trends',
          ),
          NavigationDestination(
            icon: Icon(Icons.settings_outlined, color: Colors.grey),
            selectedIcon: Icon(Icons.settings, color: Color(0xFFA01A1A)),
            label: 'Settings',
          ),
        ],
      ),
    );
  }

  Widget _buildUploadTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 48),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: const Color(0xFFFAEAEA),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: const Color(0xFFE8BEBE)),
            ),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.health_and_safety, color: Color(0xFFA01A1A), size: 36),
                SizedBox(height: 12),
                Text(
                  'Medical Report Assistant',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                ),
                SizedBox(height: 8),
                const Text(
                  '📋 We provide your report in any language that is easy to understand.',
                  style: TextStyle(fontSize: 13, color: Color(0xFF555555), height: 1.4),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(child: _buildFeatureBadge(Icons.description, 'Explain')),
              const SizedBox(width: 8),
              Expanded(child: _buildFeatureBadge(Icons.lightbulb_outline, 'Suggestions')),
              const SizedBox(width: 8),
              Expanded(child: _buildFeatureBadge(Icons.show_chart, 'Risk')),
            ],
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: _isLoading ? null : _pickFile,
            icon: const Icon(Icons.upload_file),
            label: const Text('Upload PDF Report'),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFA01A1A),
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 32),
              elevation: 4,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ),
          const SizedBox(height: 12),
          ElevatedButton.icon(
            onPressed: (_reportData == null || _isDownloadingPdf) ? null : _downloadPdf,
            icon: _isDownloadingPdf
                ? const SizedBox(
                    width: 18, height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.download_rounded),
            label: Text(_isDownloadingPdf ? 'Generating PDF...' : 'Download PDF Report'),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF1565C0),
              foregroundColor: Colors.white,
              disabledBackgroundColor: Colors.grey.shade300,
              disabledForegroundColor: Colors.grey.shade500,
              padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 32),
              elevation: 4,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'Only PDF files are supported. Tap the button above to select and upload your report.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.grey,
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 24),
          if (_isLoading)
            const Center(
              child: Column(
                children: [
                  CircularProgressIndicator(
                    color: Color(0xFFA01A1A),
                  ),
                  SizedBox(height: 16),
                  Text(
                    'Processing Report...',
                    style: TextStyle(
                      color: Colors.grey,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
          if (_reportData != null) ...[
            const SizedBox(height: 24),
            _buildResultOverview(),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: () => setState(() => _currentIndex = 2),
              icon: const Icon(Icons.tips_and_updates),
              label: const Text('Open Suggestions'),
              style: FilledButton.styleFrom(
                backgroundColor: const Color(0xFFA01A1A),
                foregroundColor: Colors.white,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildFeatureBadge(IconData icon, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFFE8BEBE)),
      ),
      child: Column(
        children: [
          Icon(icon, color: const Color(0xFFA01A1A), size: 20),
          const SizedBox(height: 6),
          Text(
            label,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
          ),
        ],
      ),
    );
  }

  Widget _buildResultOverview() {
    final risk = ((_reportData!['risk_probability'] ?? 0) as num).toDouble();
    final suggestions = _asStringList(_reportData!['translated_suggestions']);
    final hasHindiGuide = (_reportData!['disease_explanation_hi'] ?? '').toString().trim().isNotEmpty;
    final factors = _causalFactors();

    return Card(
      color: Colors.white,
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.check_circle, color: Colors.green),
                const SizedBox(width: 8),
                const Expanded(
                  child: Text(
                    'Report Processed Successfully',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                ),
                _buildStatusPill(_riskLabel(risk), _riskColor(risk)),
              ],
            ),
            const SizedBox(height: 16),
            LinearProgressIndicator(
              value: risk.clamp(0, 1).toDouble(),
              color: _riskColor(risk),
              backgroundColor: Colors.grey.shade200,
              minHeight: 8,
              borderRadius: BorderRadius.circular(99),
            ),
            const SizedBox(height: 10),
            Text(
              'Risk probability: ${(risk * 100).toStringAsFixed(1)}%',
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _buildInfoChip(Icons.translate, hasHindiGuide ? 'Hindi guide ready' : 'Basic guide ready'),
                _buildInfoChip(Icons.fact_check, '${suggestions.length} improvement steps'),
                _buildInfoChip(Icons.analytics, '${factors.length} risk factors'),
                _buildInfoChip(Icons.volume_up, 'Voice support'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusPill(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(99),
      ),
      child: Text(
        label,
        style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 12),
      ),
    );
  }

  Widget _buildInfoChip(IconData icon, String label) {
    return Chip(
      avatar: Icon(icon, size: 16, color: const Color(0xFFA01A1A)),
      label: Text(label),
      visualDensity: VisualDensity.compact,
      side: BorderSide(color: const Color(0xFFE8BEBE)),
      backgroundColor: const Color(0xFFFAEAEA),
    );
  }

  List<String> _asStringList(dynamic value) {
    if (value is List) {
      return value.map((item) => item.toString()).where((item) => item.trim().isNotEmpty).toList();
    }
    return const [];
  }

  Map<String, dynamic> _causalAnalysis() {
    final report = _reportData;
    if (report == null) return {};
    final value = report['causal_analysis'];
    if (value is Map<String, dynamic>) return value;
    if (value is String && value.trim().isNotEmpty) {
      try {
        final decoded = json.decode(value);
        if (decoded is Map<String, dynamic>) return decoded;
      } catch (_) {
        return {};
      }
    }
    return {};
  }

  List<Map<String, dynamic>> _causalFactors() {
    final factors = _causalAnalysis()['causal_factors'];
    if (factors is List) {
      return factors
          .whereType<Map>()
          .map((item) => item.map((key, value) => MapEntry(key.toString(), value)))
          .toList();
    }
    return const [];
  }

  String _riskExplanation() {
    final analysis = _causalAnalysis();
    final explanation = analysis['causal_explanation']?.toString();
    if (explanation != null && explanation.trim().isNotEmpty) return explanation;
    return 'Upload a report to see why this risk level was calculated.';
  }

  Color _riskColor(double risk) {
    if (risk < 0.35) return Colors.green;
    if (risk < 0.75) return Colors.orange;
    return Colors.red;
  }

  String _riskLabel(double risk) {
    if (risk < 0.35) return 'Low';
    if (risk < 0.75) return 'Medium';
    return 'High';
  }

  Widget _buildExplainTab() {
    if (_reportData == null) {
      return LayoutBuilder(
        builder: (context, constraints) {
          return SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 48),
            child: ConstrainedBox(
              constraints: BoxConstraints(minHeight: constraints.maxHeight),
              child: Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 32),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(24),
                        decoration: BoxDecoration(
                          color: Colors.grey.shade100,
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          Icons.description_outlined,
                          size: 64,
                          color: Colors.grey.shade400,
                        ),
                      ),
                      const SizedBox(height: 24),
                      const Text(
                        'Upload a medical report to get started',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w600,
                          color: Colors.black87,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Upload a PDF report to get started',
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.grey.shade600,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          );
        },
      );
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 48),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Medical Summary Card
          _buildSectionCard(
            title: 'MediSimple',
            icon: Icons.medical_information,
            content: _reportData!['medical_summary'] ?? 'N/A',
            canSpeak: true,
          ),
          const SizedBox(height: 16),
          
          // Simple Explanation Card
          _buildSectionCard(
            title: 'Simple Explanation',
            icon: Icons.lightbulb_outline,
            content: _reportData!['simple_explanation'] ?? 'N/A',
            canSpeak: true,
            isHighlighted: true,
          ),
          const SizedBox(height: 16),
          
          // Translated Card
          _buildSectionCard(
            title: '$_selectedLanguage Explanation',
            icon: Icons.translate,
            content: _isTranslating
                ? '⏳ Translating to $_selectedLanguage...'
                : (_reportData!['translated_explanation']?.toString().isNotEmpty == true
                    ? _reportData!['translated_explanation']
                    : 'Translation not available. Tap the language button above to retranslate.'),
            canSpeak: !_isTranslating,
            extraAction: _reportData != null && !_isTranslating
                ? IconButton(
                    icon: const Icon(Icons.refresh, size: 20),
                    tooltip: 'Retranslate',
                    color: const Color(0xFFA01A1A),
                    onPressed: () => _retranslate(_selectedLanguage),
                  )
                : null,
          ),
          const SizedBox(height: 16),
          
          // Suggestions Card
          if (_reportData!['suggestions'] != null &&
              (_reportData!['suggestions'] as List).isNotEmpty) ...[
            Builder(builder: (context) {
              final isEnglish = _selectedLanguage == 'English';
              final translatedSuggestions = _asStringList(_reportData!['translated_suggestions']);
              final showTranslated = !isEnglish && translatedSuggestions.isNotEmpty;
              final displayList = showTranslated
                  ? translatedSuggestions
                  : (_reportData!['suggestions'] as List).map((s) => s.toString()).toList();
              final title = showTranslated
                  ? '$_selectedLanguage Suggestions'
                  : 'AI Suggestions';

              return Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    title,
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  if (_isTranslating)
                    Card(
                      color: Colors.orange.shade50,
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Row(
                          children: [
                            const SizedBox(
                              width: 18, height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFFA01A1A)),
                            ),
                            const SizedBox(width: 12),
                            Text('Translating to $_selectedLanguage...',
                                style: const TextStyle(color: Colors.grey)),
                          ],
                        ),
                      ),
                    )
                  else
                    Card(
                      color: Colors.orange.shade50,
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            ...displayList.map(
                              (s) => Padding(
                                padding: const EdgeInsets.symmetric(vertical: 4),
                                child: Row(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Icon(Icons.arrow_right, color: Colors.orange),
                                    const SizedBox(width: 8),
                                    Expanded(child: Text(s)),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                ],
              );
            }),
          ],
        ],
      ),
    );
  }

  Widget _buildSuggestionsTab() {
    if (_reportData == null) {
      return _buildEmptyState(
        icon: Icons.tips_and_updates_outlined,
        title: 'Upload a report for suggestions',
        subtitle: 'After processing, this tab will show disease explanation and improvement steps in your selected language.',
      );
    }

    const Map<String, Map<String, String>> langLabels = {
      'Hindi':     {'disease': 'बीमारी की जानकारी',   'solution': 'सुधार के उपाय'},
      'Bengali':   {'disease': 'রোগের তথ্য',           'solution': 'উন্নতির উপায়'},
      'Tamil':     {'disease': 'நோய் தகவல்',           'solution': 'மேம்பாட்டு வழிகள்'},
      'Telugu':    {'disease': 'వ్యాధి సమాచారం',       'solution': 'మెరుగుదల మార్గాలు'},
      'Marathi':   {'disease': 'आजाराची माहिती',       'solution': 'सुधारणेचे उपाय'},
      'Gujarati':  {'disease': 'રોગની માહિતી',         'solution': 'સુધારાના ઉપાય'},
      'Kannada':   {'disease': 'ರೋಗದ ಮಾಹಿತಿ',         'solution': 'ಸುಧಾರಣೆಯ ಮಾರ್ಗಗಳು'},
      'Malayalam': {'disease': 'രോഗ വിവരം',            'solution': 'മെച്ചപ്പെടുത്തൽ വഴികൾ'},
    };

    final labels = langLabels[_selectedLanguage];
    final isEnglish = _selectedLanguage == 'English';

    final diseaseExplanationEn   = (_reportData!['disease_explanation_en'] ?? '').toString();
    final solutionPlanEn         = (_reportData!['solution_plan_en'] ?? '').toString();
    final diseaseExplanationLang = (_reportData!['disease_explanation_lang'] ?? _reportData!['disease_explanation_hi'] ?? '').toString();
    final solutionPlanLang       = (_reportData!['solution_plan_lang'] ?? _reportData!['solution_plan_hi'] ?? '').toString();
    final translatedSuggestions  = _asStringList(_reportData!['translated_suggestions']);
    final englishSuggestions     = _asStringList(_reportData!['suggestions']);

    final translatingText = '⏳ Translating to $_selectedLanguage...';

    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 48),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _buildSectionCard(
            title: 'Disease Explanation',
            icon: Icons.medical_information,
            content: diseaseExplanationEn.isNotEmpty
                ? diseaseExplanationEn
                : 'Disease explanation could not be generated. Please review the PDF with your doctor.',
            canSpeak: true,
            isHighlighted: true,
          ),
          const SizedBox(height: 16),
          _buildSectionCard(
            title: 'Solutions to Improve',
            icon: Icons.healing,
            content: solutionPlanEn.isNotEmpty
                ? solutionPlanEn
                : 'Follow a balanced diet, regular activity, sleep, hydration, stress control, and your doctor advice.',
            canSpeak: true,
          ),
          const SizedBox(height: 16),

          if (!isEnglish) ...[
            _buildSectionCard(
              title: labels != null
                  ? '${labels['disease']} ($_selectedLanguage)'
                  : 'Disease Explanation ($_selectedLanguage)',
              icon: Icons.menu_book,
              content: _isTranslating
                  ? translatingText
                  : diseaseExplanationLang.isNotEmpty
                      ? diseaseExplanationLang
                      : 'Translation not available. Tap refresh to retry.',
              canSpeak: !_isTranslating,
              extraAction: !_isTranslating
                  ? IconButton(
                      icon: const Icon(Icons.refresh, size: 20),
                      tooltip: 'Retranslate',
                      color: const Color(0xFFA01A1A),
                      onPressed: () => _retranslate(_selectedLanguage),
                    )
                  : null,
            ),
            const SizedBox(height: 16),
            _buildSectionCard(
              title: labels != null
                  ? '${labels['solution']} ($_selectedLanguage)'
                  : 'Solutions ($_selectedLanguage)',
              icon: Icons.spa,
              content: _isTranslating
                  ? translatingText
                  : solutionPlanLang.isNotEmpty
                      ? solutionPlanLang
                      : 'Translation not available. Tap refresh to retry.',
              canSpeak: !_isTranslating,
              extraAction: !_isTranslating
                  ? IconButton(
                      icon: const Icon(Icons.refresh, size: 20),
                      tooltip: 'Retranslate',
                      color: const Color(0xFFA01A1A),
                      onPressed: () => _retranslate(_selectedLanguage),
                    )
                  : null,
            ),
            const SizedBox(height: 16),
          ],

          if (_isTranslating)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    const SizedBox(
                      width: 18, height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFFA01A1A)),
                    ),
                    const SizedBox(width: 12),
                    Text('Translating checklist to $_selectedLanguage...',
                        style: const TextStyle(color: Colors.grey)),
                  ],
                ),
              ),
            )
          else if (translatedSuggestions.isNotEmpty && !isEnglish) ...[
            Text(
              '$_selectedLanguage Action Checklist',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            ...translatedSuggestions.asMap().entries.map(
              (entry) => _buildSuggestionTile(
                index: entry.key + 1,
                text: entry.value,
                color: const Color(0xFFA01A1A),
              ),
            ),
          ],

          if (englishSuggestions.isNotEmpty) ...[
            const SizedBox(height: 16),
            ExpansionTile(
              tilePadding: const EdgeInsets.symmetric(horizontal: 8),
              leading: const Icon(Icons.translate, color: Color(0xFFA01A1A)),
              title: const Text('Original AI Suggestions (English)'),
              children: englishSuggestions
                  .map(
                    (item) => Padding(
                      padding: const EdgeInsets.fromLTRB(8, 0, 8, 8),
                      child: _buildSuggestionTile(
                        index: englishSuggestions.indexOf(item) + 1,
                        text: item,
                        color: Colors.blueGrey,
                      ),
                    ),
                  )
                  .toList(),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildSuggestionTile({
    required int index,
    required String text,
    required Color color,
  }) {
    return Card(
      elevation: 1,
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CircleAvatar(
              radius: 14,
              backgroundColor: color.withValues(alpha: 0.14),
              child: Text(
                '$index',
                style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.bold),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                text,
                style: const TextStyle(fontSize: 14, height: 1.35),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyState({
    required IconData icon,
    required String title,
    required String subtitle,
  }) {
    return LayoutBuilder(
      builder: (context, constraints) {
        return SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 48),
          child: ConstrainedBox(
            constraints: BoxConstraints(minHeight: constraints.maxHeight),
            child: Center(
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 32),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(24),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade100,
                        shape: BoxShape.circle,
                      ),
                      child: Icon(icon, size: 64, color: Colors.grey.shade400),
                    ),
                    const SizedBox(height: 24),
                    Text(
                      title,
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w600,
                        color: Colors.black87,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      subtitle,
                      style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildSectionCard({
    required String title,
    required IconData icon,
    required String content,
    bool canSpeak = false,
    bool isHighlighted = false,
    Widget? extraAction,
  }) {
    return Card(
      color: isHighlighted ? const Color(0xFFFAEAEA) : null,
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 34,
                  height: 34,
                  decoration: BoxDecoration(
                    color: const Color(0xFFFAEAEA),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(icon, color: const Color(0xFFA01A1A), size: 20),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                if (extraAction != null) extraAction,
                if (canSpeak)
                  IconButton(
                    icon: const Icon(Icons.volume_up, color: Color(0xFFA01A1A)),
                    onPressed: () => _speak(content),
                    tooltip: 'Speak',
                  ),
              ],
            ),
            const Divider(),
            const SizedBox(height: 8),
            Text(
              content,
              style: const TextStyle(fontSize: 14, height: 1.45),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTrendsTab() {
    final factors = _causalFactors();
    final risk = _reportData != null
        ? ((_reportData!['risk_probability'] ?? 0) as num).toDouble()
        : 0.0;

    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 48),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Risk Gauge
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 42,
                        height: 42,
                        decoration: BoxDecoration(
                          color: _riskColor(risk).withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Icon(Icons.monitor_heart, color: _riskColor(risk)),
                      ),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: Text(
                          'Risk Assessment',
                          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                        ),
                      ),
                      _buildStatusPill(_riskLabel(risk), _riskColor(risk)),
                    ],
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    height: 200,
                    child: _buildRiskGauge(),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    _riskExplanation(),
                    style: TextStyle(fontSize: 13, height: 1.4, color: Colors.grey.shade700),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          
          // Temporal Analysis
          const Text(
            'Temporal Analysis',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          _buildTemporalAnalysisChart(),
          const SizedBox(height: 16),
          
          const Text(
            'Why This Risk?',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          if (factors.isNotEmpty)
            ...factors.map((factor) => _buildRiskFactorTile(factor))
          else
            const Card(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Text(
                  'Upload a report to see risk factors',
                  style: TextStyle(color: Colors.grey),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _legendDot(Color color, String label) {
    return Row(
      children: [
        Container(
          width: 10, height: 10,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(fontSize: 10, color: Colors.grey)),
      ],
    );
  }

  // ── Colour palette for time-series lines ──────────────────
  static const List<Color> _lineColors = [
    Color(0xFFA01A1A), Color(0xFF1565C0), Color(0xFF2E7D32),
    Color(0xFFE65100), Color(0xFF6A1B9A), Color(0xFF00838F),
    Color(0xFFF9A825), Color(0xFF37474F),
  ];

  Widget _buildTemporalAnalysisChart() {
    if (_reportData == null || _reportData!['temporal_analysis'] == null) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(children: [
            Icon(Icons.timeline, color: Colors.grey.shade400),
            const SizedBox(width: 12),
            const Text('Upload a report to see temporal analysis',
                style: TextStyle(color: Colors.grey)),
          ]),
        ),
      );
    }

    Map<String, dynamic> temporal = {};
    try {
      final raw = _reportData!['temporal_analysis'];
      temporal = raw is String ? json.decode(raw) : Map<String, dynamic>.from(raw);
    } catch (_) {}

    final List  trends      = temporal['trends']      is List ? temporal['trends']      as List : [];
    final List  timeSeries  = temporal['time_series'] is List ? temporal['time_series'] as List : [];
    final List  alerts      = temporal['alerts']      is List ? temporal['alerts']      as List : [];
    final String timeAnalysis = temporal['time_analysis']?.toString()    ?? '';
    final String comparisons  = temporal['comparisons']?.toString()      ?? '';
    final String pattern      = temporal['pattern_detected']?.toString() ?? '';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [

        // ════════════════════════════════════════════════════
        //  CHART 1 — TIME vs DISEASE (Line chart, multi-series)
        //  X-axis = date labels, Y-axis = actual lab values
        //  One coloured line per disease parameter
        // ════════════════════════════════════════════════════
        if (timeSeries.isNotEmpty)
          _buildTimeSeriesCard(timeSeries)
        else
          _buildNoTimeSeriesCard(timeAnalysis),

        const SizedBox(height: 12),

        // ════════════════════════════════════════════════════
        //  CHART 2 — DEVIATION BAR CHART (current report)
        //  X-axis = parameters, Y-axis = % deviation from normal
        // ════════════════════════════════════════════════════
        if (trends.isNotEmpty) _buildDeviationCard(trends),

        const SizedBox(height: 10),

        // Summary / comparison card
        if (comparisons.isNotEmpty &&
            comparisons != 'No historical comparison available')
          _buildInfoCard(Icons.compare_arrows, Colors.indigo,
              'Trend Summary', comparisons),

        if (pattern.isNotEmpty &&
            pattern != 'No persistent pattern identified') ...[
          const SizedBox(height: 8),
          _buildInfoCard(Icons.pattern, Colors.purple,
              'Pattern Detected', pattern),
        ],

        // Alerts
        if (alerts.isNotEmpty) ...[
          const SizedBox(height: 8),
          ...alerts.map((a) => _buildAlertCard(a.toString())),
        ],
      ],
    );
  }

  // ── Chart 1: Time vs Disease ─────────────────────────────
  Widget _buildTimeSeriesCard(List timeSeries) {
    // Build one LineChartBarData per parameter
    // All share the same X indices (0, 1, 2…) mapped to date labels
    final List<String> dateLabels = [];
    if (timeSeries.isNotEmpty && timeSeries[0] is Map) {
      final hist = (timeSeries[0] as Map)['history'];
      if (hist is List) {
        for (final h in hist) {
          if (h is Map) dateLabels.add(h['date']?.toString() ?? '');
        }
      }
    }
    if (dateLabels.isEmpty) return const SizedBox();

    // Build a line per parameter (cap at 8 for readability)
    final List<LineChartBarData> lines = [];
    final List<String> paramNames = [];

    for (int p = 0; p < timeSeries.length && p < 8; p++) {
      final ts = timeSeries[p];
      if (ts is! Map) continue;
      final hist   = ts['history'] as List? ?? [];
      final param  = ts['parameter']?.toString() ?? 'Param ${p+1}';
      final color  = _lineColors[p % _lineColors.length];

      final List<FlSpot> spots = [];
      for (int i = 0; i < hist.length; i++) {
        final h = hist[i];
        if (h is Map && h['value'] != null) {
          final v = (h['value'] as num).toDouble();
          spots.add(FlSpot(i.toDouble(), v));
        }
      }
      if (spots.length < 2) continue;

      paramNames.add(param);
      lines.add(LineChartBarData(
        spots: spots,
        isCurved: true,
        color: color,
        barWidth: 2.5,
        dotData: FlDotData(
          show: true,
          getDotPainter: (spot, pct, bar, idx) => FlDotCirclePainter(
            radius: 4,
            color: color,
            strokeColor: Colors.white,
            strokeWidth: 1.5,
          ),
        ),
        belowBarData: BarAreaData(
          show: true,
          color: color.withValues(alpha: 0.06),
        ),
      ));
    }

    if (lines.isEmpty) return const SizedBox();

    // Compute Y range across all spots
    double minY = double.infinity, maxY = double.negativeInfinity;
    for (final l in lines) {
      for (final s in l.spots) {
        if (s.y < minY) minY = s.y;
        if (s.y > maxY) maxY = s.y;
      }
    }
    final double yPad = ((maxY - minY) * 0.15).clamp(0.5, 50.0);
    minY = (minY - yPad).clamp(0.0, double.infinity);
    maxY = maxY + yPad;

    final double chartWidth =
        (dateLabels.length * 90.0).clamp(280.0, 800.0);

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 16, 12, 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Title
            Row(children: [
              Container(
                width: 36, height: 36,
                decoration: BoxDecoration(
                  color: const Color(0xFFA01A1A).withValues(alpha: 0.10),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.show_chart,
                    color: Color(0xFFA01A1A), size: 20),
              ),
              const SizedBox(width: 10),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Disease vs Time',
                        style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                    Text('X-axis: Visit dates  |  Y-axis: Lab value',
                        style: TextStyle(fontSize: 10, color: Colors.grey)),
                  ],
                ),
              ),
            ]),
            const SizedBox(height: 16),

            // Chart
            Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              // Rotated Y-axis label
              SizedBox(
                width: 20, height: 240,
                child: Center(
                  child: RotatedBox(
                    quarterTurns: 3,
                    child: Text('Lab Value',
                        style: TextStyle(fontSize: 10,
                            color: Colors.grey.shade500, fontWeight: FontWeight.w500)),
                  ),
                ),
              ),
              const SizedBox(width: 4),
              Expanded(
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: SizedBox(
                    width: chartWidth,
                    height: 240,
                    child: LineChart(LineChartData(
                      minY: minY,
                      maxY: maxY,
                      lineBarsData: lines,
                      borderData: FlBorderData(
                        show: true,
                        border: Border(
                          bottom: BorderSide(color: Colors.grey.shade400, width: 1.2),
                          left:   BorderSide(color: Colors.grey.shade400, width: 1.2),
                        ),
                      ),
                      gridData: FlGridData(
                        show: true,
                        drawVerticalLine: true,
                        horizontalInterval: ((maxY - minY) / 4).clamp(0.1, 999),
                        verticalInterval: 1,
                        getDrawingHorizontalLine: (_) => FlLine(
                            color: Colors.grey.shade200, strokeWidth: 0.8),
                        getDrawingVerticalLine: (_) => FlLine(
                            color: Colors.grey.shade100, strokeWidth: 0.6),
                      ),
                      titlesData: FlTitlesData(
                        // Y-axis: actual values
                        leftTitles: AxisTitles(
                          sideTitles: SideTitles(
                            showTitles: true,
                            reservedSize: 44,
                            interval: ((maxY - minY) / 4).clamp(0.1, 999),
                            getTitlesWidget: (v, meta) {
                              if (v == meta.max || v == meta.min) return const SizedBox();
                              return Text(
                                v % 1 == 0 ? v.toInt().toString() : v.toStringAsFixed(1),
                                style: TextStyle(fontSize: 9, color: Colors.grey.shade600),
                                textAlign: TextAlign.right,
                              );
                            },
                          ),
                        ),
                        rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                        topTitles:   const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                        // X-axis: date labels
                        bottomTitles: AxisTitles(
                          sideTitles: SideTitles(
                            showTitles: true,
                            reservedSize: 36,
                            interval: 1,
                            getTitlesWidget: (v, meta) {
                              final idx = v.toInt();
                              if (idx < 0 || idx >= dateLabels.length) return const SizedBox();
                              return Padding(
                                padding: const EdgeInsets.only(top: 6),
                                child: Text(dateLabels[idx],
                                    style: const TextStyle(
                                        fontSize: 9.5, fontWeight: FontWeight.w600,
                                        color: Colors.black87)),
                              );
                            },
                          ),
                        ),
                      ),
                      lineTouchData: LineTouchData(
                        touchTooltipData: LineTouchTooltipData(
                          getTooltipColor: (_) => const Color(0xFF2B2B2B),
                          getTooltipItems: (spots) {
                            return spots.map((s) {
                              final idx = s.barIndex;
                              final name = idx < paramNames.length ? paramNames[idx] : '';
                              final date = s.x.toInt() < dateLabels.length
                                  ? dateLabels[s.x.toInt()] : '';
                              return LineTooltipItem(
                                '$name\n$date: ${s.y % 1 == 0 ? s.y.toInt() : s.y.toStringAsFixed(2)}',
                                const TextStyle(color: Colors.white, fontSize: 11, height: 1.5),
                              );
                            }).toList();
                          },
                        ),
                      ),
                    )),
                  ),
                ),
              ),
            ]),

            // X-axis label
            Padding(
              padding: const EdgeInsets.only(top: 4, left: 26),
              child: Center(
                child: Text('Visit / Report Date',
                    style: TextStyle(fontSize: 10, color: Colors.grey.shade500,
                        fontWeight: FontWeight.w500)),
              ),
            ),

            const SizedBox(height: 12),

            // Colour legend — one dot per parameter
            Wrap(
              spacing: 12, runSpacing: 6,
              children: paramNames.asMap().entries.map((e) =>
                _legendDot(_lineColors[e.key % _lineColors.length], e.value)
              ).toList(),
            ),
          ],
        ),
      ),
    );
  }

  // ── Chart 2: Deviation bar chart (current report) ────────
  Widget _buildDeviationCard(List trends) {
    final List<BarChartGroupData> barGroups = [];
    final List<String> xLabels    = [];
    final List<String> fullLabels = [];
    double maxAbsDev = 100.0;

    for (int i = 0; i < trends.length; i++) {
      final t = trends[i];
      if (t is! Map) continue;

      double dev = 0.0;
      if (t['deviation_pct'] != null) {
        dev = (t['deviation_pct'] as num).toDouble().clamp(-300.0, 300.0);
      } else if (t['percent_of_normal'] != null) {
        dev = ((t['percent_of_normal'] as num).toDouble() - 100.0).clamp(-300.0, 300.0);
      }
      if (dev.abs() > maxAbsDev) maxAbsDev = dev.abs();

      final status = (t['status'] ?? 'normal').toString().toLowerCase();
      final Color barColor = dev > 0
          ? (status == 'critical' ? const Color(0xFF8B0000) : const Color(0xFFA01A1A))
          : dev < 0
              ? const Color(0xFFE65100)
              : const Color(0xFF2E7D32);

      final full  = t['parameter']?.toString() ?? 'Item ${i+1}';
      final short = full.length > 8 ? full.substring(0, 8) : full;
      xLabels.add(short);
      fullLabels.add(full);

      barGroups.add(BarChartGroupData(
        x: i,
        barRods: [
          BarChartRodData(
            fromY: 0, toY: dev,
            color: barColor,
            width: trends.length > 16 ? 7 : (trends.length > 10 ? 10 : 14),
            borderRadius: BorderRadius.only(
              topLeft:     dev >= 0 ? const Radius.circular(4) : Radius.zero,
              topRight:    dev >= 0 ? const Radius.circular(4) : Radius.zero,
              bottomLeft:  dev <  0 ? const Radius.circular(4) : Radius.zero,
              bottomRight: dev <  0 ? const Radius.circular(4) : Radius.zero,
            ),
          ),
        ],
      ));
    }

    final double yMax      = (maxAbsDev * 1.2).ceilToDouble();
    final double yInterval = yMax <= 100 ? 25 : (yMax <= 200 ? 50 : 100);
    final double barWidth  = trends.length > 16 ? 9.0 : (trends.length > 10 ? 13.0 : 18.0);
    final double chartWidth = (trends.length * (barWidth + 14)).clamp(300.0, 2000.0);

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 16, 12, 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Container(
                width: 36, height: 36,
                decoration: BoxDecoration(
                  color: const Color(0xFFA01A1A).withValues(alpha: 0.10),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.bar_chart_rounded,
                    color: Color(0xFFA01A1A), size: 20),
              ),
              const SizedBox(width: 10),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Lab Value Deviation from Normal',
                        style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                    Text('Y-axis: % deviation  |  0 = normal midpoint  |  ±100 = range boundary',
                        style: TextStyle(fontSize: 10, color: Colors.grey)),
                  ],
                ),
              ),
            ]),
            const SizedBox(height: 16),

            Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              SizedBox(
                width: 20, height: 280,
                child: Center(
                  child: RotatedBox(
                    quarterTurns: 3,
                    child: Text('% Deviation from Normal',
                        style: TextStyle(fontSize: 10, color: Colors.grey.shade500,
                            fontWeight: FontWeight.w500)),
                  ),
                ),
              ),
              const SizedBox(width: 4),
              Expanded(
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: SizedBox(
                    width: chartWidth, height: 280,
                    child: BarChart(BarChartData(
                      maxY: yMax, minY: -yMax,
                      alignment: BarChartAlignment.spaceAround,
                      barGroups: barGroups,
                      borderData: FlBorderData(
                        show: true,
                        border: Border(
                          bottom: BorderSide(color: Colors.grey.shade400, width: 1),
                          left:   BorderSide(color: Colors.grey.shade400, width: 1),
                          top:    BorderSide(color: Colors.grey.shade400, width: 1),
                        ),
                      ),
                      gridData: FlGridData(
                        show: true,
                        drawVerticalLine: false,
                        horizontalInterval: yInterval,
                        getDrawingHorizontalLine: (value) {
                          if (value == 0) {
                            return const FlLine(color: Color(0xFFA01A1A), strokeWidth: 2.0);
                          }
                          if (value == 100 || value == -100) {
                            return FlLine(
                                color: Colors.orange.withValues(alpha: 0.5),
                                strokeWidth: 1.2, dashArray: [6, 4]);
                          }
                          return FlLine(color: Colors.grey.shade200, strokeWidth: 0.7);
                        },
                      ),
                      titlesData: FlTitlesData(
                        leftTitles: AxisTitles(
                          sideTitles: SideTitles(
                            showTitles: true,
                            reservedSize: 42,
                            interval: yInterval,
                            getTitlesWidget: (value, meta) {
                              if (value == meta.max || value == meta.min) return const SizedBox();
                              final label = value == 0
                                  ? 'Normal'
                                  : '${value > 0 ? "+" : ""}${value.toInt()}%';
                              return Text(label,
                                  style: TextStyle(
                                    fontSize: 9,
                                    fontWeight: value == 0 ? FontWeight.bold : FontWeight.normal,
                                    color: value == 0
                                        ? const Color(0xFFA01A1A)
                                        : value > 0
                                            ? const Color(0xFFA01A1A).withValues(alpha: 0.7)
                                            : Colors.orange.shade700,
                                  ),
                                  textAlign: TextAlign.right);
                            },
                          ),
                        ),
                        rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                        topTitles:   const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                        bottomTitles: AxisTitles(
                          sideTitles: SideTitles(
                            showTitles: true,
                            reservedSize: 48,
                            getTitlesWidget: (value, meta) {
                              final idx = value.toInt();
                              if (idx < 0 || idx >= xLabels.length) return const SizedBox();
                              return Transform.rotate(
                                angle: -0.5,
                                child: Text(xLabels[idx],
                                    style: const TextStyle(fontSize: 8.5, color: Colors.black87),
                                    overflow: TextOverflow.ellipsis),
                              );
                            },
                          ),
                        ),
                      ),
                      barTouchData: BarTouchData(
                        touchTooltipData: BarTouchTooltipData(
                          maxContentWidth: 190,
                          getTooltipColor: (_) => const Color(0xFF2B2B2B),
                          getTooltipItem: (group, groupIndex, rod, rodIndex) {
                            if (groupIndex >= trends.length) return null;
                            final t      = trends[groupIndex] as Map;
                            final name   = fullLabels[groupIndex];
                            final val    = t['value']           ?? '—';
                            final unit   = t['unit']            ?? '';
                            final status = (t['status'] ?? '—').toString().toUpperCase();
                            final ref    = t['reference_range'] ?? '—';
                            final dev    = t['deviation_pct'] != null
                                ? '${(t['deviation_pct'] as num) >= 0 ? "+" : ""}${(t['deviation_pct'] as num).toStringAsFixed(1)}% from normal'
                                : '';
                            return BarTooltipItem(
                              '$name\nValue: $val $unit\nRef: $ref\nStatus: $status\n$dev',
                              const TextStyle(color: Colors.white, fontSize: 11, height: 1.5),
                            );
                          },
                        ),
                      ),
                    )),
                  ),
                ),
              ),
            ]),

            Padding(
              padding: const EdgeInsets.only(top: 4, left: 26),
              child: Center(
                child: Text('Lab Parameters (scroll to see all)',
                    style: TextStyle(fontSize: 10, color: Colors.grey.shade500,
                        fontWeight: FontWeight.w500)),
              ),
            ),

            const SizedBox(height: 10),

            Wrap(spacing: 14, runSpacing: 6, children: [
              _legendDot(const Color(0xFF2E7D32), 'Normal (0)'),
              _legendDot(const Color(0xFFA01A1A), 'High (+)'),
              _legendDot(const Color(0xFFE65100), 'Low (-)'),
              _legendDot(const Color(0xFF8B0000), 'Critical'),
            ]),
          ],
        ),
      ),
    );
  }

  Widget _buildNoTimeSeriesCard(String timeAnalysis) {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Icon(Icons.show_chart, size: 40, color: Colors.grey.shade300),
            const SizedBox(height: 8),
            Text(
              timeAnalysis.isNotEmpty
                  ? timeAnalysis
                  : 'No multi-visit data found.\nUpload reports containing a trend summary table (with dates like Jan, Feb, May) to see time vs disease chart.',
              style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoCard(IconData icon, Color color, String title, String body) {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: color.withValues(alpha: 0.8), size: 20),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title,
                      style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold,
                          color: color.withValues(alpha: 0.9))),
                  const SizedBox(height: 4),
                  Text(body, style: const TextStyle(fontSize: 13)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAlertCard(String alert) {
    return Card(
      elevation: 1,
      color: Colors.red.shade50,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Icon(Icons.warning_amber_rounded, color: Colors.red.shade400, size: 20),
            const SizedBox(width: 10),
            Expanded(
              child: Text(alert,
                  style: TextStyle(fontSize: 13, color: Colors.red.shade700)),
            ),
          ],
        ),
      ),
    );
  }

    Widget _buildRiskFactorTile(Map<String, dynamic> factor) {
    final label = factor['factor']?.toString() ?? 'Risk factor';
    final cause = factor['cause']?.toString() ?? '';
    final probability = factor['probability'];
    final percent = probability is num ? '${(probability * 100).toStringAsFixed(0)}%' : '';

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 34,
              height: 34,
              decoration: BoxDecoration(
                color: Colors.amber.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(Icons.priority_high, color: Colors.amber.shade800, size: 20),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          label,
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                        ),
                      ),
                      if (percent.isNotEmpty) _buildStatusPill(percent, Colors.blueGrey),
                    ],
                  ),
                  if (cause.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Text(
                      cause,
                      style: TextStyle(fontSize: 13, height: 1.35, color: Colors.grey.shade700),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRiskGauge() {
    double risk = _reportData != null
        ? (_reportData!['risk_probability'] ?? 0).toDouble()
        : 0.0;
    
    Color riskColor;
    String riskLevel;
    
    if (risk < 0.35) {
      riskColor = Colors.green;
      riskLevel = 'Low';
    } else if (risk < 0.75) {
      riskColor = Colors.orange;
      riskLevel = 'Medium';
    } else {
      riskColor = Colors.red;
      riskLevel = 'High';
    }
    
    return Stack(
      alignment: Alignment.center,
      children: [
        PieChart(
          PieChartData(
            sectionsSpace: 0,
            centerSpaceRadius: 60,
            startDegreeOffset: 180,
            sections: [
              PieChartSectionData(
                value: risk * 100,
                color: riskColor,
                radius: 30,
                showTitle: false,
              ),
              PieChartSectionData(
                value: (1 - risk) * 100,
                color: Colors.grey.shade300,
                radius: 30,
                showTitle: false,
              ),
            ],
          ),
        ),
        Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              '${(risk * 100).toStringAsFixed(0)}%',
              style: TextStyle(
                fontSize: 32,
                fontWeight: FontWeight.bold,
                color: riskColor,
              ),
            ),
            Text(
              riskLevel,
              style: TextStyle(
                fontSize: 16,
                color: riskColor,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildSettingsTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 48),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Company Info Card
          Card(
            elevation: 4,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  // Company Logo
                  ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: Image.asset(
                      'assets/images/medisimple_logo.jpg',
                      width: 80,
                      height: 80,
                      fit: BoxFit.cover,
                    ),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'MediSimple',
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const Text(
                    'Your Personal Health Expert',
                    style: TextStyle(color: Colors.grey),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Version 2.0.0',
                    style: TextStyle(color: Colors.grey),
                  ),
                ],
              ),
            ),
          ),
          Card(
            child: ListTile(
              leading: const Icon(Icons.language, color: Color(0xFFA01A1A)),
              title: const Text('Output Language'),
              subtitle: Text(_selectedLanguage),
              trailing: const Icon(Icons.chevron_right),
              onTap: _showLanguageSelector,
            ),
          ),
          
          // TTS Settings
          Card(
            child: ListTile(
              leading: const Icon(Icons.record_voice_over, color: Color(0xFFA01A1A)),
              title: const Text('Text-to-Speech'),
              subtitle: Text(_ttsEnabled ? 'Enabled' : 'Disabled'),
              trailing: Switch(
                value: _ttsEnabled,
                onChanged: (value) async {
                  setState(() {
                    _ttsEnabled = value;
                  });
                  if (value) {
                    await _applyVoiceForLanguage(_selectedLanguage);
                  } else {
                    await _tts.stop();
                  }
                },
                activeThumbColor: const Color(0xFFA01A1A),
              ),
            ),
          ),
          Card(
            child: ListTile(
              leading: const Icon(Icons.headphones, color: Color(0xFFA01A1A)),
              title: const Text('Voice Model'),
              subtitle: Text(_selectedVoiceName ?? 'Default'),
              trailing: const Icon(Icons.chevron_right),
              onTap: _showVoiceSelector,
            ),
          ),
          
          // About
          Card(
            child: ListTile(
              leading: const Icon(Icons.info_outline, color: Color(0xFFA01A1A)),
              title: const Text('About'),
              subtitle: const Text('System information'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {
                showAboutDialog(
                  context: context,
                  applicationName: 'MediSimple',
                  applicationVersion: '2.0.0',
                  applicationLegalese: '© 2026 MediSimple',
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _tts.stop();
    _pollingTimer?.cancel();
    super.dispose();
  }
}
