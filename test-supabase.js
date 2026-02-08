// Test Supabase connection
const { createClient } = require('@supabase/supabase-js');

const SUPABASE_URL = 'https://wkzlezxxtbqfodyustav.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indremxlenh4dGJxZm9keXVzdGF2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDI5MDQ2MiwiZXhwIjoyMDg1ODY2NDYyfQ.5Feoao-TeAUJfACWS4qdlGW8nc0K0ewD0OBQQOJ5ny4';

async function test() {
  console.log('Testing Supabase connection...');

  const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

  // Test 1: List buckets
  console.log('\n1. Listing buckets...');
  const { data: buckets, error: bucketsError } = await supabase.storage.listBuckets();
  if (bucketsError) {
    console.log('Error listing buckets:', bucketsError);
  } else {
    console.log('Buckets:', buckets.map(b => b.name));
  }

  // Test 2: Upload a test file
  console.log('\n2. Uploading test file...');
  const testData = Buffer.from('Hello from test ' + Date.now());
  const filename = `test_${Date.now()}.txt`;

  const { data: uploadData, error: uploadError } = await supabase.storage
    .from('thumbnails')
    .upload(filename, testData, {
      contentType: 'text/plain',
      upsert: true
    });

  if (uploadError) {
    console.log('Upload error:', uploadError);
  } else {
    console.log('Upload success:', uploadData);

    // Get public URL
    const { data: urlData } = supabase.storage
      .from('thumbnails')
      .getPublicUrl(filename);

    console.log('Public URL:', urlData.publicUrl);
  }

  // Test 3: List files in thumbnails bucket
  console.log('\n3. Listing files in thumbnails bucket...');
  const { data: files, error: filesError } = await supabase.storage
    .from('thumbnails')
    .list();

  if (filesError) {
    console.log('Error listing files:', filesError);
  } else {
    console.log('Files:', files.slice(0, 10).map(f => f.name));
  }
}

test().catch(console.error);
