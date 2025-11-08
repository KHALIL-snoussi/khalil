import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:universal_html/html.dart' as html;
import '../models/preview_response.dart';
import '../services/api.dart';

class DownloadScreen extends StatefulWidget {
  final String jobId;
  final String style;
  final CropRect cropRect;
  final int rotateDeg;
  final GridSize grid;

  const DownloadScreen({
    super.key,
    required this.jobId,
    required this.style,
    required this.cropRect,
    required this.rotateDeg,
    required this.grid,
  });

  @override
  State<DownloadScreen> createState() => _DownloadScreenState();
}

class _DownloadScreenState extends State<DownloadScreen> {
  final ApiService _api = ApiService();
  bool _isLoading = true;
  bool _isDownloaded = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _generateFinal();
  }

  Future<void> _generateFinal() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      // Create request
      final request = FinalRequest(
        jobId: widget.jobId,
        style: widget.style,
        grid: widget.grid,
        paletteId: '${widget.style}_v1',
        crop: widget.cropRect,
        rotateDeg: widget.rotateDeg,
        options: ProcessingOptions(),
      );

      // Call API
      final zipBytes = await _api.generateFinal(request: request);

      // Trigger download
      _downloadFile(zipBytes, 'diamond_pattern_${widget.style}.zip');

      setState(() {
        _isLoading = false;
        _isDownloaded = true;
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to generate final pattern: $e';
        _isLoading = false;
      });
    }
  }

  void _downloadFile(Uint8List bytes, String filename) {
    // Create blob and download link
    final blob = html.Blob([bytes]);
    final url = html.Url.createObjectUrlFromBlob(blob);
    final anchor = html.AnchorElement(href: url)
      ..setAttribute('download', filename)
      ..click();
    html.Url.revokeObjectUrl(url);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Download Pattern'),
      ),
      body: Center(
        child: Container(
          constraints: const BoxConstraints(maxWidth: 600),
          padding: const EdgeInsets.all(32),
          child: _isLoading
              ? const Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    CircularProgressIndicator(),
                    SizedBox(height: 16),
                    Text(
                      'Generating your pattern...',
                      style: TextStyle(fontSize: 18),
                    ),
                    SizedBox(height: 8),
                    Text(
                      'This may take a few seconds',
                      style: TextStyle(color: Colors.grey),
                    ),
                  ],
                )
              : _errorMessage != null
                  ? Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.error_outline,
                            size: 64, color: Colors.red),
                        const SizedBox(height: 16),
                        Text(_errorMessage!),
                        const SizedBox(height: 16),
                        ElevatedButton(
                          onPressed: _generateFinal,
                          child: const Text('Retry'),
                        ),
                      ],
                    )
                  : _buildSuccessView(),
        ),
      ),
    );
  }

  Widget _buildSuccessView() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Icon(
          Icons.check_circle_outline,
          size: 100,
          color: Colors.green,
        ),
        const SizedBox(height: 32),
        const Text(
          'Pattern Downloaded!',
          style: TextStyle(
            fontSize: 28,
            fontWeight: FontWeight.bold,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 16),
        const Text(
          'Your diamond painting pattern pack has been downloaded.',
          style: TextStyle(fontSize: 16, color: Colors.grey),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 48),
        const Card(
          child: Padding(
            padding: EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Your package includes:',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
                SizedBox(height: 12),
                Row(
                  children: [
                    Icon(Icons.picture_as_pdf, size: 20),
                    SizedBox(width: 8),
                    Expanded(child: Text('pattern.pdf - Full grid pattern with legend')),
                  ],
                ),
                SizedBox(height: 8),
                Row(
                  children: [
                    Icon(Icons.image, size: 20),
                    SizedBox(width: 8),
                    Expanded(child: Text('preview.png - Preview image')),
                  ],
                ),
                SizedBox(height: 8),
                Row(
                  children: [
                    Icon(Icons.table_chart, size: 20),
                    SizedBox(width: 8),
                    Expanded(child: Text('counts.csv - Color counts and bag codes')),
                  ],
                ),
                SizedBox(height: 8),
                Row(
                  children: [
                    Icon(Icons.code, size: 20),
                    SizedBox(width: 8),
                    Expanded(child: Text('spec.json - Technical specifications')),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 32),
        ElevatedButton.icon(
          onPressed: () {
            // Navigate back to home
            Navigator.popUntil(context, (route) => route.isFirst);
          },
          icon: const Icon(Icons.home),
          label: const Text('Create Another Pattern'),
          style: ElevatedButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 16),
          ),
        ),
      ],
    );
  }
}
