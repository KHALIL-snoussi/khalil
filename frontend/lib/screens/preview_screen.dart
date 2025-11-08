import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../models/preview_response.dart';
import '../services/api.dart';
import 'download_screen.dart';

class PreviewScreen extends StatefulWidget {
  final Uint8List imageBytes;
  final String filename;
  final CropRect cropRect;
  final int rotateDeg;

  const PreviewScreen({
    super.key,
    required this.imageBytes,
    required this.filename,
    required this.cropRect,
    required this.rotateDeg,
  });

  @override
  State<PreviewScreen> createState() => _PreviewScreenState();
}

class _PreviewScreenState extends State<PreviewScreen> {
  final ApiService _api = ApiService();
  bool _isLoading = true;
  String? _errorMessage;
  PreviewResponse? _response;

  @override
  void initState() {
    super.initState();
    _loadPreviews();
  }

  Future<void> _loadPreviews() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      // Create payload
      final payload = PreviewPayload(
        crop: widget.cropRect,
        rotateDeg: widget.rotateDeg,
        grid: GridSize(w: 100, h: 140),
        styles: ['original', 'vintage', 'popart'],
        options: ProcessingOptions(),
      );

      // Call API
      final response = await _api.generatePreviews(
        imageBytes: widget.imageBytes,
        filename: widget.filename,
        payload: payload,
      );

      setState(() {
        _response = response;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to generate previews: $e';
        _isLoading = false;
      });
    }
  }

  void _selectStyle(String style) {
    if (_response == null) return;

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => DownloadScreen(
          jobId: _response!.jobId,
          style: style,
          cropRect: widget.cropRect,
          rotateDeg: widget.rotateDeg,
          grid: _response!.grid,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Preview Styles'),
      ),
      body: _isLoading
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text('Generating previews...'),
                  SizedBox(height: 8),
                  Text(
                    'This may take a few seconds',
                    style: TextStyle(color: Colors.grey),
                  ),
                ],
              ),
            )
          : _errorMessage != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline,
                          size: 64, color: Colors.red),
                      const SizedBox(height: 16),
                      Text(_errorMessage!),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadPreviews,
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              : _buildPreviewGrid(),
    );
  }

  Widget _buildPreviewGrid() {
    if (_response == null) return const SizedBox.shrink();

    final styles = _response!.previews.keys.toList();

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Card(
            color: Colors.blue,
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                children: [
                  Icon(Icons.info_outline, color: Colors.white, size: 32),
                  SizedBox(height: 8),
                  Text(
                    'Select a style to continue',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  SizedBox(height: 4),
                  Text(
                    'Click on a preview to download the final pattern pack',
                    style: TextStyle(color: Colors.white70),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          ...styles.map((style) => _buildStyleCard(style)),
        ],
      ),
    );
  }

  Widget _buildStyleCard(String style) {
    final preview = _response!.previews[style]!;
    final counts = _response!.counts[style]!;
    final totalCells = counts.reduce((a, b) => a + b);

    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => _selectStyle(style),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Preview image
            Image.memory(
              _base64ToBytes(preview),
              fit: BoxFit.contain,
              height: 400,
            ),

            // Style info
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        _styleTitle(style),
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      ElevatedButton.icon(
                        onPressed: () => _selectStyle(style),
                        icon: const Icon(Icons.download),
                        label: const Text('Download'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _styleDescription(style),
                    style: const TextStyle(color: Colors.grey),
                  ),
                  const SizedBox(height: 12),
                  Text('Grid: ${_response!.grid.w} × ${_response!.grid.h}'),
                  Text('Total cells: $totalCells'),
                  const SizedBox(height: 12),
                  const Text(
                    'Color counts:',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 4),
                  Wrap(
                    spacing: 8,
                    runSpacing: 4,
                    children: List.generate(
                      7,
                      (i) => Chip(
                        label: Text('B${i + 1:02d}: ${counts[i]}'),
                        visualDensity: VisualDensity.compact,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _styleTitle(String style) {
    switch (style) {
      case 'original':
        return 'Original';
      case 'vintage':
        return 'Vintage';
      case 'popart':
        return 'Pop Art';
      default:
        return style;
    }
  }

  String _styleDescription(String style) {
    switch (style) {
      case 'original':
        return 'Neutral grayscale palette with warm skin tones';
      case 'vintage':
        return 'Warm sepia tones for a classic look';
      case 'popart':
        return 'Bold, saturated colors for vibrant patterns';
      default:
        return '';
    }
  }

  Uint8List _base64ToBytes(String base64String) {
    // Remove data URL prefix if present
    final base64Data = base64String.split(',').last;
    return Uri.parse('data:image/png;base64,$base64Data')
        .data!
        .contentAsBytes();
  }
}
