# Teste de conexão TCP usando PowerShell/.NET
$tcpClient = New-Object System.Net.Sockets.TcpClient
try {
    Write-Host "Testando conexao TCP para localhost:5432..."
    $result = $tcpClient.ConnectAsync("localhost", 5432).Wait(5000)
    if ($result) {
        Write-Host "Conexao TCP bem-sucedida!"
    } else {
        Write-Host "Timeout na conexao TCP"
    }
} catch {
    Write-Host "Erro na conexao TCP: $($_.Exception.Message)"
} finally {
    $tcpClient.Close()
}
