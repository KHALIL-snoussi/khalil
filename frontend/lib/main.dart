import 'package:flutter/material.dart';
import 'screens/upload_screen.dart';
import 'services/api.dart';

void main() {
  runApp(const DiamondPaintingApp());
}

class DiamondPaintingApp extends StatelessWidget {
  const DiamondPaintingApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Diamond Painting Generator',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.blue,
          brightness: Brightness.light,
        ),
      ),
      home: const UploadScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}
