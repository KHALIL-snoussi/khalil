import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:extended_image/extended_image.dart';
import '../models/preview_response.dart';
import 'preview_screen.dart';

class CropScreen extends StatefulWidget {
  final Uint8List imageBytes;
  final String filename;

  const CropScreen({
    super.key,
    required this.imageBytes,
    required this.filename,
  });

  @override
  State<CropScreen> createState() => _CropScreenState();
}

class _CropScreenState extends State<CropScreen> {
  final GlobalKey<ExtendedImageEditorState> _editorKey =
      GlobalKey<ExtendedImageEditorState>();

  double _rotation = 0;
  bool _isProcessing = false;

  void _rotateLeft() {
    setState(() {
      _rotation -= 90;
      if (_rotation < 0) _rotation += 360;
    });
  }

  void _rotateRight() {
    setState(() {
      _rotation += 90;
      if (_rotation >= 360) _rotation -= 360;
    });
  }

  Future<void> _continue() async {
    setState(() {
      _isProcessing = true;
    });

    try {
      // Get crop rectangle
      final editorState = _editorKey.currentState;
      if (editorState == null) return;

      final cropRect = editorState.getCropRect();
      if (cropRect == null) {
        // Use full image if no crop
        final image = await _decodeImage(widget.imageBytes);
        final crop = CropRect(
          x: 0,
          y: 0,
          w: image.width,
          h: image.height,
        );

        if (mounted) {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => PreviewScreen(
                imageBytes: widget.imageBytes,
                filename: widget.filename,
                cropRect: crop,
                rotateDeg: _rotation.toInt(),
              ),
            ),
          );
        }
        return;
      }

      // Get original image dimensions
      final image = await _decodeImage(widget.imageBytes);

      // Convert crop rect to source coordinates
      final crop = CropRect(
        x: cropRect.left.toInt(),
        y: cropRect.top.toInt(),
        w: cropRect.width.toInt(),
        h: cropRect.height.toInt(),
      );

      if (mounted) {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => PreviewScreen(
              imageBytes: widget.imageBytes,
              filename: widget.filename,
              cropRect: crop,
              rotateDeg: _rotation.toInt(),
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    } finally {
      setState(() {
        _isProcessing = false;
      });
    }
  }

  Future<ui.Image> _decodeImage(Uint8List bytes) async {
    final codec = await ui.instantiateImageCodec(bytes);
    final frame = await codec.getNextFrame();
    return frame.image;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Crop & Rotate'),
        actions: [
          TextButton.icon(
            onPressed: _isProcessing ? null : _continue,
            icon: _isProcessing
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.arrow_forward),
            label: const Text('Continue'),
            style: TextButton.styleFrom(foregroundColor: Colors.white),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: Container(
              color: Colors.black,
              child: ExtendedImage.memory(
                widget.imageBytes,
                key: _editorKey,
                fit: BoxFit.contain,
                mode: ExtendedImageMode.editor,
                extendedImageEditorKey: _editorKey,
                initEditorConfigHandler: (state) {
                  return EditorConfig(
                    maxScale: 8.0,
                    cropRectPadding: const EdgeInsets.all(20.0),
                    hitTestSize: 20.0,
                    cropAspectRatio: 100 / 140, // Portrait aspect ratio
                  );
                },
              ),
            ),
          ),
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.grey.shade100,
            child: Column(
              children: [
                const Text(
                  'Adjust the crop area to portrait aspect ratio (100:140)',
                  style: TextStyle(fontSize: 14, color: Colors.grey),
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    ElevatedButton.icon(
                      onPressed: _rotateLeft,
                      icon: const Icon(Icons.rotate_left),
                      label: const Text('Rotate Left'),
                    ),
                    ElevatedButton.icon(
                      onPressed: _rotateRight,
                      icon: const Icon(Icons.rotate_right),
                      label: const Text('Rotate Right'),
                    ),
                    ElevatedButton.icon(
                      onPressed: () {
                        _editorKey.currentState?.reset();
                      },
                      icon: const Icon(Icons.refresh),
                      label: const Text('Reset'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
