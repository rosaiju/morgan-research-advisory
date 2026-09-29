$ErrorActionPreference='Stop'
$manifestRoot=$PSScriptRoot
$locks=Get-Content -LiteralPath (Join-Path $manifestRoot 'evaluation-source-lock.json') -Raw | ConvertFrom-Json
$sourceDir=Join-Path $manifestRoot 'evaluation-sources'
New-Item -ItemType Directory -Path $sourceDir -Force | Out-Null
$requests=@()
foreach($row in $locks){
  if($row.kind -eq 'dataset'){
    $paths=@('README.md')
    if($row.id -eq 'HuggingFaceH4/MATH-500'){$paths+= 'test.jsonl'}
    foreach($p in $paths){$requests += @{url=('https://huggingface.co/datasets/'+$row.id+'/resolve/'+$row.revision+'/'+$p);name=($row.id.Replace('/','--')+'__'+$p)}}
  }
}
$ghFiles=@{
 'google-deepmind/bbeh'=@('README.md','bbeh/evaluate.py')
 'google-research/google-research'=@('instruction_following_eval/data/input_data.jsonl','instruction_following_eval/evaluation_lib.py','instruction_following_eval/instructions.py','instruction_following_eval/instructions_registry.py','instruction_following_eval/instructions_util.py','instruction_following_eval/requirements.txt')
 'UKGovernmentBEIS/inspect_evals'=@('src/inspect_evals/mmlu_pro/mmlu_pro.py','src/inspect_evals/bbeh/bbeh.py','src/inspect_evals/ifeval/ifeval.py')
 'huggingface/Math-Verify'=@('src/math_verify/parser.py','src/math_verify/grader.py','src/math_verify/__init__.py','pyproject.toml')
}
foreach($repo in $ghFiles.Keys){
 $rev=($locks | Where-Object id -eq $repo).revision
 foreach($p in $ghFiles[$repo]){$requests+=@{url=('https://raw.githubusercontent.com/'+$repo+'/'+$rev+'/'+$p);name=($repo.Replace('/','--')+'__'+$p.Replace('/','__'))}}
}
$requests+=@{url='https://huggingface.co/moonshotai/Kimi-K3/resolve/f831ab66814297da540d832a5235f8e904f29d06/encoding_k3.py';name='kimi_encoding_k3.py'}
$records=foreach($r in $requests){
 $target=Join-Path $sourceDir $r.name
 try{
  Invoke-WebRequest -UseBasicParsing -Uri $r.url -OutFile $target -TimeoutSec 30
  [pscustomobject]@{url=$r.url;file=$r.name;sha256=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLower();status='fetched'}
 }catch{[pscustomobject]@{url=$r.url;file=$r.name;status='failed';error=$_.Exception.Message}}
}
$records | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $manifestRoot 'evaluation-files-lock.json') -Encoding utf8
$records | Select-Object file,status | ConvertTo-Json
