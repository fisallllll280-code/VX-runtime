// Developer example only. Never hardcode credentials: use protected app configuration/Keychain.
// Verify server certificate and hostname with the platform URLSession trust evaluation.
import Foundation
import CryptoKit

struct VXAsset: Decodable {
    let name: String
    let sha256: String
    let bytes: Int
    let path: String
}

struct VXManifest: Decodable {
    let schema: String
    let items: [VXAsset]
}

func fetchVXAsset(endpoint: URL, token: String, item: VXAsset) async throws -> Data {
    guard endpoint.scheme == "https",
          let assetURL = URL(string: item.path, relativeTo: endpoint)?.absoluteURL,
          assetURL.scheme == "https",
          assetURL.host == endpoint.host,
          assetURL.port == endpoint.port else {
        throw URLError(.badURL)
    }
    guard item.bytes >= 0 && item.bytes <= 16 * 1024 * 1024 else {
        throw URLError(.dataLengthExceedsMaximum)
    }
    var request = URLRequest(url: assetURL)
    request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
    let (data, response) = try await URLSession.shared.data(for: request)
    guard let http = response as? HTTPURLResponse,
          http.statusCode == 200,
          http.url?.host == endpoint.host,
          http.url?.scheme == "https",
          http.url?.port == endpoint.port else {
        throw URLError(.badServerResponse)
    }
    guard data.count == item.bytes else { throw URLError(.cannotDecodeRawData) }
    let digest = SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
    guard digest == item.sha256.lowercased() else { throw URLError(.cannotDecodeRawData) }
    return data
}
