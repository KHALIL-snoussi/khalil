import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import '../models/preview_response.dart';

class ApiService {
  final String baseUrl;

  ApiService({this.baseUrl = 'http://localhost:8000'});

  /// Check API health
  Future<bool> checkHealth() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/health'));
      return response.statusCode == 200;
    } catch (e) {
      print('Health check failed: $e');
      return false;
    }
  }

  /// Generate previews for multiple styles
  Future<PreviewResponse> generatePreviews({
    required Uint8List imageBytes,
    required String filename,
    required PreviewPayload payload,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/preview');

      // Create multipart request
      final request = http.MultipartRequest('POST', uri);

      // Add image file
      request.files.add(http.MultipartFile.fromBytes(
        'image',
        imageBytes,
        filename: filename,
      ));

      // Add payload as JSON string
      request.fields['payload'] = jsonEncode(payload.toJson());

      // Send request
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final jsonData = jsonDecode(response.body);
        return PreviewResponse.fromJson(jsonData);
      } else {
        throw Exception('Preview generation failed: ${response.body}');
      }
    } catch (e) {
      print('Error generating previews: $e');
      rethrow;
    }
  }

  /// Generate final pattern pack
  Future<Uint8List> generateFinal({
    required FinalRequest request,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/final');

      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(request.toJson()),
      );

      if (response.statusCode == 200) {
        return response.bodyBytes;
      } else {
        throw Exception('Final generation failed: ${response.body}');
      }
    } catch (e) {
      print('Error generating final: $e');
      rethrow;
    }
  }
}
